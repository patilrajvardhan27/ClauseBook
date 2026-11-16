import { useEffect, useState } from "react";
import { createClient, type FindingOut, type PlaybookOut } from "@clausebook/api-client";
import { FindingCard, Skeleton } from "@clausebook/ui";
import { locateSegment } from "./word/locate";
import { highlightRange } from "./word/highlight";
import { applyRedline } from "./word/applyRedline";
import { WhyPanel } from "./WhyPanel";

const client = createClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? "https://localhost:8000" });

// The task pane: read the document, start a review, stream findings,
// highlight each clause in place, and apply a tracked change on request.
export default function TaskPane() {
  const [supported, setSupported] = useState(true);
  const [playbooks, setPlaybooks] = useState<PlaybookOut[] | null>(null);
  const [findings, setFindings] = useState<FindingOut[]>([]);
  const [activeFindingId, setActiveFindingId] = useState<string | null>(null);

  useEffect(() => {
    setSupported(Office.context.requirements.isSetSupported("WordApi", "1.4"));
    client.listPlaybooks().then(setPlaybooks).catch(() => setPlaybooks([]));
  }, []);

  async function handleStartReview(playbookId: string) {
    const text = await Word.run(async (context) => {
      context.document.body.load("text");
      await context.sync();
      return context.document.body.text;
    });

    const document = await client.uploadDocument(new File([text], "document.txt"));
    const review = await client.startReview(document.id, playbookId);

    const source = client.openReviewEventStream(review.id);
    source.addEventListener("finding_ready", async (event) => {
      const { finding_id } = JSON.parse((event as MessageEvent).data);
      const finding = await client.getFinding(finding_id);
      setFindings((prev) => [...prev, finding]);
      await highlightFinding(finding);
    });
  }

  async function highlightFinding(finding: FindingOut): Promise<void> {
    await Word.run(async (context) => {
      const segmentText = finding.evidence.segment_text ?? "";
      if (!segmentText) return;
      const range = await locateSegment(context, segmentText);
      if (!range) return;
      const status = finding.proposed_position_id
        ? finding.matched_position_id
          ? "fallback_proposed"
          : "outside_playbook"
        : "in_playbook";
      highlightRange(range, status);
      await context.sync();
    });
  }

  async function handleApply(finding: FindingOut): Promise<void> {
    const segmentText = finding.evidence.segment_text ?? "";
    const hunks = finding.redline.hunks ?? [];
    if (!segmentText || hunks.length === 0) return;

    await Word.run(async (context) => {
      const range = await locateSegment(context, segmentText);
      if (!range) return;
      await applyRedline(context, range, hunks);
    });
  }

  if (!supported) {
    return <p>This version of Word does not support the WordApi 1.4 requirement set Clausebook needs.</p>;
  }

  return (
    <div style={{ padding: "1rem", fontFamily: "system-ui" }}>
      <h2 style={{ fontFamily: "Newsreader, serif" }}>Clausebook</h2>
      {!playbooks ? (
        <Skeleton height={28} />
      ) : (
        <select onChange={(e) => handleStartReview(e.target.value)} defaultValue="">
          <option value="" disabled>
            Start a review with…
          </option>
          {playbooks.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      )}

      {findings.map((finding) => (
        <div key={finding.id} onClick={() => setActiveFindingId(finding.id)}>
          <FindingCard finding={finding} />
          {activeFindingId === finding.id && (
            <>
              <WhyPanel finding={finding} />
              <button onClick={() => handleApply(finding)}>Apply as tracked change</button>
            </>
          )}
        </div>
      ))}
    </div>
  );
}
