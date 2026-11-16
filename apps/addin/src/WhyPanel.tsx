import type { FindingOut } from "@clausebook/api-client";

// Matched position, target position, extracted terms and the precedent
// used -- the plan's "Why" panel, so Accept is never a leap of faith.
export function WhyPanel({ finding }: { finding: FindingOut }) {
  return (
    <div className="cb-panel" style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}>
      <p>
        <strong>Reason:</strong> {finding.evidence.reason ?? "No rule-based reason recorded."}
      </p>
      {finding.evidence.better_attributes && finding.evidence.better_attributes.length > 0 && (
        <p>
          <strong>Better on:</strong> {finding.evidence.better_attributes.join(", ")}
        </p>
      )}
      <p>
        <strong>Extracted terms:</strong>
      </p>
      <pre className="cb-mono" style={{ fontSize: "0.75rem" }}>{JSON.stringify(finding.attrs, null, 2)}</pre>
      {finding.evidence.precedent_hits && finding.evidence.precedent_hits.length > 0 && (
        <p>
          <strong>Precedent:</strong>{" "}
          {finding.evidence.precedent_hits.map((hit) => hit.precedent_id).join(", ")}
        </p>
      )}
    </div>
  );
}
