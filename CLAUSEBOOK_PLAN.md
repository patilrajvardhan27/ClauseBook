# Clausebook: Build Plan

Contract review that knows a firm's playbook. Clausebook reads a counterparty draft, finds each clause, places it against the firm's ordered positions (preferred, fallbacks, walk-away), and proposes the right fallback as a minimal tracked change in Word, with the precedent it came from.

Target: Draftwise, Forward Deployed AI Engineer (Backend). Build time: 10 days at 5 to 6 focused hours a day.

---

## 1. The problem, stated precisely

A partner says "our fallbacks never come out right." Underneath that sentence are four separate failures, and each one is a design requirement:

| Failure | Why it happens in naive tools | Clausebook's answer |
|---|---|---|
| Wrong clause type | Classifier trained on headings; real clauses hide under "Miscellaneous" | Classify clause text, not headings; multi-label; per-class thresholds |
| Wrong position detected | Text similarity says "close to fallback 1" when the cap is actually 3x, not 1x | Extract the deal terms (cap multiple, notice days, carve-outs) and compare them by rule |
| Wrong fallback chosen | Picks the most similar approved text, not the most favorable acceptable one | Positions are ordered; choose the best position the counterparty text has not already beaten, filtered by deal context |
| Bad redline | Replaces the whole clause; lawyers reject it | Word-level minimal diff from counterparty text to target language, inserted as tracked changes |

Interview line: "Fallback selection is a ranking problem over an ordered set with conditions, not a retrieval problem. Retrieval only supplies evidence."

---

## 2. Scope

**Must ship (days 1 to 8)**
1. Legal ontology in Postgres: firm, playbook, clause type, ordered positions, attributes, approved language, precedent.
2. Ingestion of CUAD into bronze, silver and gold layers.
3. Clause segmentation and multi-label classification (baseline plus fine-tuned transformer).
4. Hybrid retrieval in OpenSearch (BM25 plus kNN, fused), with a reranker.
5. Review service: segment, classify, extract terms, place on playbook, choose fallback, build redline.
6. Evaluation harness with a committed test set and CI quality gates.
7. Word add-in (Office.js, React, TypeScript) that highlights deviations and inserts tracked changes.
8. Web app: review results, playbook editor, analytics, Terms, Privacy.

**Should ship (days 9 to 10)**
9. Performance pass on a 100-page contract, before and after numbers.
10. Market analytics from the CUAD corpus (what is "standard" for each term).

**Stretch**
11. Neo4j projection of the ontology for precedent traversal.
12. Active learning loop from reviewer accept and reject actions.
13. AWS deployment (Terraform).

---

## 3. Data

| Dataset | What it is | License | Use |
|---|---|---|---|
| CUAD v1 | 510 commercial contracts from EDGAR, lawyer-labeled spans for 41 clause categories | CC BY 4.0 | Segment and classify training data, precedent corpus, market stats |
| ACORD | 126,000+ expert-rated query and clause pairs, 9 categories | CC BY 4.0 | Retrieval evaluation (NDCG@k) |
| MAUD | 152 merger agreements, 92 deal points | CC BY 4.0 | Stretch: second domain to test the ontology |
| Sample playbooks | 8 playbooks written by you from public drafting guidance | Yours | Positions and approved language; labeled "sample" in the UI |
| Gold placements | 150 clauses hand-labeled with the correct playbook position | Yours | Position and fallback accuracy |

Rules:
- Record source URL, download date, license and attribution for every dataset in `docs/data-sources.md`. CC BY 4.0 requires attribution in the app's About page.
- Sample playbooks are not any firm's real guidance. Say so on screen.
- Gold labels: label all 150 yourself, then ask one law student to label 50 of them blind. Report Cohen's kappa. If kappa is under 0.6, tighten the position definitions and relabel. This is the strongest single answer to "how do you know your labels are right."

**Eight clause types for v1** (chosen because they have measurable terms):

| Clause type (CUAD category) | Extracted attributes |
|---|---|
| Cap on Liability | cap_basis (fees paid, fixed amount), cap_multiple, lookback_months, carve_outs[] |
| Uncapped Liability | carve_outs[] |
| Termination for Convenience | who_may_terminate, notice_days |
| Notice Period to Terminate Renewal | notice_days |
| Renewal Term | auto_renew (bool), renewal_months |
| Governing Law | jurisdiction |
| Anti-Assignment | consent_required, change_of_control_trigger |
| Audit Rights | frequency_per_year, notice_days, cost_bearer |

---

## 4. Ontology

### 4.1 Entities and why each exists

| Entity | Why it exists (the answer for the interview) |
|---|---|
| Firm | Tenant boundary. Every row below carries `firm_id`, enforced by Postgres row-level security. |
| Playbook | A firm can hold several (buy side, sell side, by practice group). Versioned, because guidance changes and old reviews must stay explainable. |
| ClauseType | Shared vocabulary mapped to CUAD categories, so training data and firm guidance meet on one key. |
| Attribute | The measurable parts of a clause type. Comparing numbers by rule is reliable; comparing prose is not. |
| Position | One ordered stance on a clause type: rank 0 preferred, 1..n fallbacks, last is walk-away. Holds conditions per attribute. |
| AppliesWhen | Deal context that switches a position on or off (party role, deal size band, counterparty type). This is what most tools leave out. |
| ApprovedLanguage | The text a lawyer may insert for a position. Several variants per position, each with a source. |
| Precedent | A real clause instance (from CUAD or a firm's executed deals) linked to the position it satisfies. Gives "we accepted this before, in deal X." |
| Review / Finding | One run over one document and one result per clause, with the evidence and the decision trail. |

### 4.2 Schema (Postgres 16)

```
firm(id, name)
playbook(id, firm_id, name, side, version, published_at)
clause_type(id, cuad_category, name)
attribute(id, clause_type_id, key, kind)              -- kind: number | enum | bool | list
position(id, playbook_id, clause_type_id, rank, label, is_walk_away)
position_condition(id, position_id, attribute_id, op, value_json)   -- op: <=, >=, =, in, contains_all
applies_when(id, position_id, key, op, value_json)     -- party_role, deal_size_band, counterparty_type
approved_language(id, position_id, text, source_note)
precedent(id, firm_id null, source, document_id, clause_text, clause_type_id, position_id null, attrs_json)
document(id, firm_id, sha256, title, pages, uploaded_at)
segment(id, document_id, ord, start_char, end_char, text, heading)
review(id, document_id, playbook_id, playbook_version, status, started_at, finished_at, cost_tokens)
finding(id, review_id, segment_id, clause_type_id, confidence, attrs_json,
        matched_position_id, proposed_position_id, redline_json, evidence_json, decision, decided_by)
job(id, kind, payload_json, status, attempts, run_after, locked_at)   -- Postgres job queue
outbox_event(id, aggregate, type, payload_json, created_at, published_at)
```

- `position_condition` and `applies_when` hold logic as data, so a forward deployed engineer changes a firm's guidance with no code change.
- Migrations with Alembic. Never edit an applied migration.
- `finding.evidence_json` stores the retrieved precedent ids, extracted attribute spans and rule results, so every proposal can be explained.

### 4.3 Fallback selection (the core algorithm)

```
place(clause, playbook, deal_context):
  attrs   = extract(clause)                         # deterministic first, model only if needed
  ladder  = positions for clause_type, ordered by rank, filtered by applies_when(deal_context)
  matched = first position in ladder whose conditions all pass on attrs     # where the text sits now
  if matched is rank 0: no change
  target  = best position (lowest rank) not already rejected in this negotiation
            and strictly better than matched for at least one attribute
  if matched is None (worse than walk-away): flag "outside playbook", target = walk-away, escalate
  redline = minimal_diff(clause.text, approved_language(target) adapted to attrs)
```

- "Strictly better" uses a per-attribute direction stored on `attribute` (lower notice days is better for one side, higher for the other; `side` on the playbook flips it).
- Rejected positions come from the decision history on prior findings for the same counterparty and document family, which prevents re-proposing a fallback the other side already refused.

---

## 5. ML, DL and data concepts, mapped to the work

| Stage | Concept (roadmap.sh area) | Technique | How it is evaluated |
|---|---|---|---|
| Ingestion | Data engineering: medallion layout, idempotency | Bronze raw files keyed by SHA-256; silver normalized text and CUAD spans; gold segments with labels | Re-run adds 0 rows; Pandera checks on every silver table |
| Segmentation | Data cleaning, rules, sequence labeling | Numbering and heading patterns, then sentence boundaries; stretch: CRF over line features | Boundary F1 against CUAD span edges |
| Labels from spans | Feature engineering | A segment gets every CUAD category whose labeled span overlaps it by 50% or more | Spot-check 100 segments by hand |
| Classifier baseline | Classical ML (Data Mining, ML) | TF-IDF word and character n-grams, one-vs-rest logistic regression, class weights | Per-class precision, recall, AUPR; precision at 80% recall (CUAD's own metric) |
| Classifier v2 | NNDL: transformers, fine-tuning | Fine-tune `nlpaueb/legal-bert-base-uncased` (or DeBERTa-v3-small) multi-label with BCE, class weights for rare labels, early stopping, per-class thresholds tuned on validation | Same metrics; must beat baseline macro AUPR or it does not ship |
| Leakage control | ML evaluation | GroupKFold by contract, so segments from one contract never sit in train and test | Documented split; test set frozen and hashed |
| Calibration | ML | Temperature scaling on validation logits | Reliability diagram, expected calibration error |
| Inference speed | NNDL deployment | Export to ONNX, int8 dynamic quantization, batch by length | Latency per 100 segments before and after; accuracy drop under 1 point |
| Term extraction | NLP, rules | Regex and spaCy patterns for numbers, durations, money, jurisdictions; LLM with Pydantic schema only when rules return nothing | Exact-match accuracy per attribute on gold set |
| Retrieval | Information retrieval | OpenSearch BM25 plus kNN on `bge-small-en-v1.5` embeddings, fused with reciprocal rank fusion, filtered by clause type; `bge-reranker-base` cross-encoder on top 50 | NDCG@5 and Recall@20 on ACORD; ablation table: BM25, kNN, hybrid, hybrid plus rerank |
| Placement | Rules engine over ontology | Section 4.3 | Position accuracy and fallback accuracy on 150 gold clauses; confusion matrix by rank |
| Comparison and wording | LLM systems | LLM only adapts approved language to extracted terms and explains the deviation; output validated by schema; every cited precedent id must exist in the evidence | Recorded runs replayed in CI; human pass rate on 40 sampled redlines |
| Redline | Text diff | Word-level diff (diff-match-patch), merge small hunks | Edit distance vs full replacement; reviewer acceptance rate |
| Unusual clauses | Unsupervised learning | k-means on embeddings per clause type; distance from centroid as an outlier score ("negotiation trap" flag) | Precision@20 on hand review |
| Market stats | Data analysis | Percentiles of cap multiple, notice days, renewal months across the CUAD corpus | Matches a pandas recomputation in a test |
| Clause co-occurrence | Data mining | Apriori on clause presence per contract; report rules with lift above 1.5 ("contracts with uncapped IP indemnity usually carry audit rights") | Support, confidence, lift table in the analytics page |
| Feedback loop (stretch) | Active learning | Queue lowest-margin predictions for review; retrain thresholds weekly | Labels gained per hour of review |

---

## 6. System architecture

```
                        +-------------------------------+
 Word (Office.js task   |  apps/addin  (React, TS)      |----+
 pane)                  +-------------------------------+    |   REST + SSE
                        +-------------------------------+    |   (shared api-client)
 Browser                |  apps/web    (React, TS)      |----+
                        +-------------------------------+    |
                                                             v
                        +---------------------------------------------+
                        |  services/api  (FastAPI)                    |
                        |  auth, playbooks, documents, reviews, SSE   |
                        |  writes job + outbox rows in one tx         |
                        +--------------------+------------------------+
                                             |
              +------------------------------+-----------------------------+
              v                              v                             v
   +---------------------+      +--------------------------+     +-------------------+
   | PostgreSQL 16       |      | services/worker (Python) |     | OpenSearch 2.x    |
   | ontology, reviews,  |<---->| SKIP LOCKED job queue:    |<--->| precedent index   |
   | jobs, outbox, RLS   |      | parse > segment >         |     | BM25 + kNN,       |
   +---------------------+      | classify (ONNX) > extract |     | hybrid pipeline   |
              ^                 | > retrieve > place >      |     +-------------------+
              |                 | redline                   |              ^
              |                 +-------------+-------------+              |
              |                               | LLM calls (bounded,        |
              |                               v  cached, recorded)         |
              |                     +-------------------+                  |
              |                     | LLM provider via  |                  |
              |                     | LiteLLM           |                  |
              |                     +-------------------+                  |
              |                                                            |
              +---- outbox relay (worker) -- indexes precedent changes ----+

 pipelines/ (Python): CUAD, ACORD > bronze > silver > gold; loads precedent and training data
 ml/        (Python): training, evaluation, ONNX export, model cards
 Observability: OpenTelemetry traces per stage, Prometheus metrics (latency, tokens, cost per document)
```

Key decisions (each gets an ADR in `docs/adr/`):
1. **Postgres job queue (`FOR UPDATE SKIP LOCKED`) instead of a broker.** One less system; jobs and their state commit in the same transaction as the review. Revisit past ~50 jobs per second.
2. **Outbox to OpenSearch.** Postgres is the source of truth for precedent; OpenSearch is a derived index that can be rebuilt. No dual writes.
3. **Rules before models.** Deterministic extraction and placement run first; the model fills gaps. Cheaper, faster, explainable, and testable without a key.
4. **Results stream as clauses finish.** SSE events per finding, so a lawyer sees the first clause in seconds on a long document.
5. **Row-level security per firm.** Tenant isolation lives in the database, not only in application code.
6. **Customer documents are never used for training.** Training uses CUAD only; firm data only feeds that firm's precedent index.

---

## 7. Repository layout and DRY rules

```
clausebook/
  apps/
    web/                 React + TS + Vite
    addin/               Office.js task pane, React + TS
  packages/
    ui/                  shared components, tokens, Skeleton, FindingCard, DiffView
    api-client/          TS types generated from OpenAPI, fetch + SSE helpers
  services/
    api/                 FastAPI: routers/, domain/, repo/, auth/, sse/
    worker/              stages/ (one module per stage), queue.py, outbox.py
  libs/
    clausebook_core/     shared Python: ontology models, placement engine, diff, config, db session
  pipelines/             bronze/, silver/, gold/, checks/
  ml/                    classify/, retrieve/, extract/, eval/, export/
  eval/                  fixtures/ (frozen test set, recorded LLM runs), thresholds.yaml
  contracts/openapi/     split by tag: playbooks, documents, reviews, analytics
  db/migrations/
  deploy/                docker-compose.yml, opensearch/, otel/, terraform/ (stretch)
  docs/                  adr/, data-sources.md, model-cards/, ontology.md, demo-script.md
  scripts/               verify.sh, check-file-length.mjs, record_runs.py
```

**DRY rules**
- One placement engine in `libs/clausebook_core`, imported by the API (for preview) and the worker (for runs). Never a second copy.
- One OpenAPI spec generates both the Python response models check and the TypeScript client used by web and add-in.
- `packages/ui` is shared by the web app and the add-in; the add-in never re-implements a FindingCard or DiffView.
- Every worker stage implements one interface: `run(ctx: ReviewContext) -> StageResult`. Timing, retries, tracing and caching wrap the interface once.
- Thresholds live in `eval/thresholds.yaml`, read by both CI and the eval CLI.
- Before adding a helper, search `libs/`, `packages/` and `services/*/domain`. If logic appears twice, extract it in the same PR.

**250-line limit**
- `scripts/check-file-length.mjs` fails CI for any source file over 250 lines (generated code, lockfiles and fixtures excluded).
- Split by responsibility when a file passes about 200 lines: router vs service vs repository; one stage per file; one component per file.

---

## 8. API (contract first)

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/documents` | Upload .docx or .pdf; returns id; dedupes by SHA-256 |
| POST | `/v1/reviews` | Start a review `{document_id, playbook_id, deal_context}`; returns 202 |
| GET | `/v1/reviews/{id}/events` | SSE: `segment_found`, `finding_ready`, `progress`, `done`, `error` |
| GET | `/v1/reviews/{id}` | Full results with evidence |
| PATCH | `/v1/findings/{id}` | Accept, reject (with reason) or edit; feeds rejected-position history |
| GET/POST/PATCH | `/v1/playbooks`, `/v1/playbooks/{id}/positions` | Playbook editor; publishing creates a new version |
| POST | `/v1/playbooks/{id}/preview` | Place a pasted clause without running a full review |
| GET | `/v1/search?q=&clause_type=` | Hybrid precedent search |
| GET | `/v1/analytics/market/{clause_type}` | Percentiles and distributions from the corpus |
| GET | `/v1/analytics/overrides` | Reviewer acceptance and override rates by clause type and position |

Errors use RFC 9457 problem+json. Pagination is uniform. Every write is idempotent with an `Idempotency-Key` header.

---

## 9. Word add-in

- Office.js, React, TypeScript, Vite; manifest for Word on the web and desktop. Sideload with a Microsoft 365 developer tenant.
- Flow: read body text and paragraphs, send to `/v1/reviews`, stream findings over SSE, then for each finding:
  - Locate the clause: `body.search()` accepts at most 255 characters, so search the first 200 characters of the segment, then expand the range paragraph by paragraph to the segment end.
  - Highlight by status (in playbook, fallback proposed, outside playbook) using `range.font.highlightColor`.
  - On "Apply": set `document.changeTrackingMode = trackAll` (WordApi 1.4 or later) and apply the diff hunks with `insertText` on sub-ranges, so the lawyer sees a normal tracked redline.
  - "Why" panel: matched position, target position, extracted terms with their source spans, and the precedent used.
- Feature-detect API sets with `Office.context.requirements.isSetSupported`; show a clear message if the host is too old.

---

## 10. Evaluation harness

`clausebook eval` runs everything below and writes `eval/report.md` plus JSON. CI runs it on every pull request.

| Suite | Data | Metrics | CI gate (set from your first honest run, then hold) |
|---|---|---|---|
| Segmentation | CUAD test contracts | Boundary F1 | No drop over 2 points |
| Classification | CUAD test split (grouped by contract) | Per-class AUPR, P@80%R, macro F1 | No class drops over 3 points; macro may not drop |
| Extraction | 150 gold clauses | Exact match per attribute | No drop |
| Retrieval | ACORD | NDCG@5, Recall@20 | No drop over 2 points |
| Placement | 150 gold clauses | Matched-position accuracy, fallback accuracy, rank confusion | No drop |
| Redlines | 40 sampled findings | Human pass rate (recorded once), edit size vs full replace | Report only |
| Cost and latency | 3 fixed contracts (5, 30, 100 pages) | p50 and p95 per stage, tokens per document | p95 may not regress over 20% |

- LLM calls are recorded once to `eval/fixtures/` with the prompt hash; CI replays them, so the suite needs no API key and is deterministic. A separate manual workflow re-records with a live key.
- The frozen test set is hashed; CI fails if the file changes without a version bump.
- Every prompt lives in a file with a version; changing a prompt without re-running eval is blocked by a CI check on the prompt hash.

---

## 11. Performance plan

1. Instrument each stage with OpenTelemetry spans and record a baseline on the 100-page contract.
2. Expected hot spots and fixes:
   - Classification: batch by sequence length, ONNX int8, run on CPU threads.
   - Retrieval: one `_msearch` per batch of clauses instead of one query per clause.
   - LLM: run only on clauses that are not rank 0; bounded concurrency; cache by `sha256(clause_text + playbook_version + prompt_version)`.
   - Parsing: cache parsed segments by document SHA-256.
3. Report before and after: total p95, time to first finding, tokens and cost per document.

---

## 12. Web app

Pages: Review (document, findings list, diff view, why panel), Playbooks (ordered ladder editor per clause type, conditions as form rows, preview box), Search (hybrid precedent search with filters), Analytics (market percentiles, co-occurrence rules, override rates), About (data sources, attributions, non-affiliation notice), Terms of Service, Privacy Policy.

Forms validate on the client with zod and on the server with Pydantic; errors appear next to the field and in a summary at the top. Every async region has a skeleton. Accessibility: WCAG 2.2 AA, keyboard reorder for positions, Playwright with axe in CI.

---

## 13. Design direction

Draftwise's site reads as premium and editorial: short imperative headlines, a product-first structure (hero, product walk-through in Draft, Review, Negotiate sections, security, customers, closing call to action), product video instead of illustration, and alternating light and dark sections. Clausebook follows that register and information structure with its own name, copy, palette and type. No Draftwise name, logo, wording or screenshots; the footer reads "Independent portfolio project. Not affiliated with or endorsed by Draftwise."

| Token | Value | Use |
|---|---|---|
| `--cb-paper` | #F4F1EA | Page background (warm, not pure white) |
| `--cb-surface` | #FBFAF6 | Panels, tables |
| `--cb-ink` | #1A1D21 | Body text |
| `--cb-ink-muted` | #5A5F66 | Secondary text |
| `--cb-night` | #13202B | Dark sections, add-in header |
| `--cb-green` | #1E5B4A | Primary actions, "in playbook" |
| `--cb-amber` | #9A5B00 | "Fallback proposed" text |
| `--cb-red` | #A3271F | "Outside playbook" text |
| `--cb-line` | #D8D3C8 | 1px rules |

- Type: Newsreader (headlines) and Public Sans (UI), IBM Plex Mono for clause ids. Self-hosted.
- Rectangular panels, 2px radius, 1px rules, no shadows, gradients, glass, orbs or dot grids, no icon library (text labels), no hover animations, no emojis.
- Landing page shows the real product: a 40-second recording of a review in Word, then a static walk-through of one clause going from counterparty text to tracked fallback. No testimonials, no pricing tiers.
- Check every text color against its background for 4.5:1 before shipping.

---

## 14. DevOps

- `docker compose up` runs Postgres, OpenSearch (single node, security plugin configured), the API, the worker, the web app and an OTel collector with a local Grafana stack.
- GitHub Actions: lint (ruff, mypy, eslint, tsc), file length check, unit tests, Testcontainers integration tests (Postgres, OpenSearch), eval suite with gates, Playwright and axe, CodeQL, dependency audit, image build with a vulnerability scan.
- Stretch AWS: Terraform for ECS Fargate (API, worker), RDS Postgres, Amazon OpenSearch Service (a single small managed domain is far cheaper than Serverless, which bills a minimum capacity around the clock; check current pricing), S3 for uploads, Secrets Manager. Deploy by OIDC from GitHub, no stored keys. Tear down after recording the demo.

---

## 15. Repository hygiene

- Commit messages describe the change in plain past tense ("Added hybrid retrieval with reciprocal rank fusion"). No tool signatures, co-author trailers or generated banners in commits, PRs, code or docs.
- Any local tool or agent guidance file stays out of the repo (add it to `.git/info/exclude`).
- Code comments explain why, not what. No filler words ("robust", "seamless", "leverage"), no emojis, no em dashes.
- README in the voice of the engineer who built it: what it does, how to run it, what the numbers are, what is synthetic, known limits.

---

## 16. Ten-day schedule

| Day | Work | Done when |
|---|---|---|
| 1 | Repo, guardrails, compose, OpenAPI skeleton, migrations V1 to V4, ADRs 1 to 3 | CI green; `\dt` shows the ontology |
| 2 | Pipelines: CUAD and ACORD bronze, silver, gold; Pandera checks; data-sources doc | Re-run adds 0 rows |
| 3 | Segmentation and span-to-label mapping; baseline classifier with grouped split | Baseline report committed |
| 4 | Fine-tuned transformer, calibration, ONNX export, model card | Beats baseline macro AUPR or is dropped |
| 5 | OpenSearch index, outbox relay, hybrid search with RRF, reranker, ACORD eval | Ablation table committed |
| 6 | Eight sample playbooks, term extraction, placement engine, 150 gold labels | Placement accuracy reported |
| 7 | Review worker end to end, SSE, LLM wording with recorded runs, minimal diff | First full review streams in the browser |
| 8 | Word add-in: locate, highlight, tracked-change apply, why panel | Demo in Word on the web |
| 9 | Web app pages, playbook editor, analytics, Terms, Privacy, axe tests | Playwright and axe green |
| 10 | Performance pass, eval gates in CI, README, 3-minute demo video | Before and after numbers in README |

Cut order if behind: active learning, Neo4j, AWS, co-occurrence rules, k-means outliers. Never cut the eval harness or the add-in.

---

## 17. Resume bullets (fill brackets only from your own runs)

- **Clausebook (link):** Contract review service (Python/FastAPI, PostgreSQL, OpenSearch) that places each clause on a firm's ordered playbook and proposes the right fallback as a tracked change in a **Word add-in** (Office.js, React/TypeScript); legal **ontology** with positions, deal-context conditions and precedent stored as data.
- **Retrieval + ML:** hybrid **BM25 + kNN** search fused with RRF and a cross-encoder reranker reached **NDCG@5 [x]** on ACORD; fine-tuned **Legal-BERT** multi-label classifier at **[x] macro AUPR** vs **[x]** for TF-IDF baseline on a contract-grouped CUAD split; ONNX int8 cut inference **[x] to [y] ms**.
- **Evaluation as tests:** **[x]%** fallback accuracy on **150** hand-labeled clauses (kappa **[x]** with a second annotator); recorded LLM runs replay in CI so quality gates run with no API key; 100-page contract p95 **[x] to [y] s**.

---

## 18. Interview preparation

- Walk the ontology: why `applies_when` exists, why positions are ordered, why attributes beat text similarity, what you would change for a firm whose playbook is a 40-page Word document.
- Failure modes you found: segments split mid-sentence, nested carve-outs, caps defined by reference ("the amount in Schedule B"), clauses that mix two types.
- Where the model helped and where it cost time: name one prompt change that looked better by eye and lost on the eval.
- What you would ask a knowledge management lead in the first meeting: who owns the playbook, how fallbacks are approved, how rejected positions are tracked today, which clause types cause the most escalations.
