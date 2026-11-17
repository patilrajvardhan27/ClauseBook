# Problems and solutions

Issues hit while building ClauseBook, grouped by area. Each one lists the symptom, the cause and the fix.

## Data and evaluation

### Headings did not predict clause type
**Problem.** The first classifier idea was to read the section heading. It failed on real contracts.  
**Cause.** Across the headed segments in CUAD, 94.8% carried a label their heading did not name.  
**Solution.** Classification used the clause text only. The disagreement rate was kept as a reported metric, so the premise stays measurable.

### Random splits inflated every score
**Problem.** A random train/test split gave scores that looked too good.  
**Cause.** Contracts reuse boilerplate. Near-duplicate clauses landed on both sides of the split.  
**Solution.** Every evaluation split with `GroupKFold` on `contract_id`. The Legal-BERT script imported the same loader and fold count as the baseline, so both models saw identical data.

### The expected baseline number was wrong
**Problem.** The Legal-BERT target was written down as 0.5 macro precision.  
**Cause.** The number was a guess made before the baseline ran on the full corpus.  
**Solution.** The measured TF-IDF baseline was 0.599 macro precision and 0.579 macro F1 across 5 folds. All comparisons used those figures.

## Backend and storage

### Writes were silently discarded
**Problem.** API calls returned success, but nothing persisted.  
**Cause.** The database session dependency never committed. Every request rolled back when the session closed.  
**Solution.** The session committed on a successful request and rolled back on an exception.

### Upload failed on a missing firm
**Problem.** Document upload raised a foreign key violation on a fresh database.  
**Cause.** The document row referenced a firm that did not exist yet.  
**Solution.** Upload created the owning firm record before inserting the document.

### The worker parsed empty documents
**Problem.** Uploaded files reached the worker, but the parse stage had no text.  
**Cause.** Nothing stored the file bytes. The stage only saw a database row.  
**Solution.** A local blob store held the bytes, and the parse stage read them back by key. `.txt` and `.docx` both went through it.

### ACORD precedents did not fit the schema
**Problem.** Seeding ACORD clauses failed on a NOT NULL constraint.  
**Cause.** ACORD clauses carried no ontology clause type, but `precedent.clause_type_id` required one.  
**Solution.** A migration made the column nullable, and the seeder left it empty.

### The search index could drift from Postgres
**Problem.** A lost OpenSearch index had no recovery path.  
**Cause.** Postgres was the source of truth, but nothing could replay changes into the index.  
**Solution.** Writes went through a transactional outbox. A test deleted the live 8,955-document index, replayed the outbox and checked that the rebuilt count matched exactly.

## Retrieval

### Single retrievers scored low
**Problem.** BM25 alone reached nDCG@5 of 0.151 and kNN alone reached 0.146 on ACORD.  
**Cause.** Lexical match missed paraphrase, and dense match missed exact legal terms.  
**Solution.** Reciprocal rank fusion over both lifted nDCG@5 to 0.180. A cross-encoder rerank on top reached 0.193.

## Legal-BERT fine-tuning

### Training would not start
**Problem.** `Trainer` crashed during setup with an ImportError.  
**Cause.** `accelerate` was not installed, and the `ml` extra did not list it.  
**Solution.** `accelerate>=1.1` was added to the `ml` extra in `pyproject.toml`.

### The model predicted nothing
**Problem.** After two epochs, macro precision was 0.024 and macro F1 was 0.004.  
**Cause.** Forty-one mostly rare labels, plain binary cross-entropy and a fixed 0.5 cutoff. The easiest way to cut loss was to predict negative everywhere. Loss still fell, which hid the problem.  
**Solution.** Three changes:
- Per-label positive weights in the loss, using the damped negative-to-positive ratio, capped at 10.
- A higher learning rate (5e-5) with warmup.
- A decision threshold picked on a validation slice of each fold's training contracts. The held-out fold was never used for tuning.

The first completed fold then scored 0.600 macro precision and 0.566 macro F1.

### A renamed training argument
**Problem.** `TrainingArguments` rejected `warmup_ratio`.  
**Cause.** The installed `transformers` major version removed it.  
**Solution.** The script used `warmup_steps=0.1`, which that version reads as a fraction of total steps. A short smoke run on 400 rows caught it before the long job started.

### The run slowed to a crawl
**Problem.** Step time went from 1.4 s to 22 s partway through fold 1.  
**Cause.** One long-lived process kept each finished fold's model and device memory. Swap reached 9.2 GB of 10 GB on a 16 GB machine.  
**Solution.** Each fold ran in a fresh subprocess, wrote its own `metrics.json` and model, and was skipped on restart if already done. Step time returned to 1.4 s.

## Code quality

### Duplicated loader
**Problem.** The Legal-BERT script carried its own copy of the gold-segment loader.  
**Cause.** It was written beside the baseline instead of reusing it.  
**Solution.** It imported `load_gold_rows` and `N_FOLDS` from `ml/classify/train.py`. There is one definition of the data and the split.

### A comment that overstated the code
**Problem.** The script header said the worker's classify stage already loaded the saved model.  
**Cause.** The stage's ONNX path was still a stub that called the baseline.  
**Solution.** The header was corrected to say the stage still served the baseline.

### File length
**Problem.** Long files were hard to review.  
**Solution.** `scripts/check-file-length.mjs` failed the build above 250 lines, and every source file stayed under it.
