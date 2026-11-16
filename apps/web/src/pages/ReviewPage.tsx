import { useEffect, useState } from "react";
import { createClient, type FindingOut, type PlaybookOut } from "@clausebook/api-client";
import { FindingCard, Skeleton } from "@clausebook/ui";

const client = createClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? "" });

// Lets a lawyer pick an uploaded document and a playbook, start a review,
// and watch findings arrive. The SSE wiring here mirrors what the add-in's
// task pane does against the same endpoint.
export default function ReviewPage() {
  const [playbooks, setPlaybooks] = useState<PlaybookOut[] | null>(null);
  const [findings, setFindings] = useState<FindingOut[]>([]);
  const [reviewId, setReviewId] = useState<string | null>(null);
  const [selectedPlaybookId, setSelectedPlaybookId] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);

  useEffect(() => {
    client.listPlaybooks().then((result) => {
      setPlaybooks(result);
      if (result[0]) setSelectedPlaybookId(result[0].id);
    }).catch(() => setPlaybooks([]));
  }, []);

  async function handleStartReview(event: React.FormEvent) {
    event.preventDefault();
    if (!file || !selectedPlaybookId) return;
    const document = await client.uploadDocument(file);
    const review = await client.startReview(document.id, selectedPlaybookId);
    setFindings([]);
    setReviewId(review.id);
  }

  useEffect(() => {
    if (!reviewId) return;
    const source = client.openReviewEventStream(reviewId);
    source.addEventListener("finding_ready", (event) => {
      const { finding_id } = JSON.parse((event as MessageEvent).data);
      client.getFinding(finding_id).then((finding) => setFindings((prev) => [...prev, finding]));
    });
    source.addEventListener("done", () => source.close());
    return () => source.close();
  }, [reviewId]);

  async function handleDecision(findingId: string, decision: "accepted" | "rejected") {
    const updated = await client.decideFinding(findingId, decision);
    setFindings((prev) => prev.map((f) => (f.id === updated.id ? updated : f)));
  }

  return (
    <section>
      <h1>Review</h1>
      <p style={{ color: "var(--cb-ink-muted)" }}>
        Upload a counterparty draft, pick a playbook, and see each clause placed against it.
      </p>

      {!playbooks ? (
        <Skeleton height={32} width={240} />
      ) : (
        <form onSubmit={handleStartReview} style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <input type="file" accept=".docx,.pdf" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          <select value={selectedPlaybookId} onChange={(e) => setSelectedPlaybookId(e.target.value)}>
            {playbooks.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <button type="submit" disabled={!file}>
            Start review
          </button>
        </form>
      )}

      {findings.map((finding) => (
        <FindingCard
          key={finding.id}
          finding={finding}
          onDecide={(decision) => handleDecision(finding.id, decision)}
        />
      ))}

      {reviewId === null && (
        <p style={{ color: "var(--cb-ink-muted)" }}>
          No review running yet. The same flow also runs from the Word add-in's task pane.
        </p>
      )}
    </section>
  );
}
