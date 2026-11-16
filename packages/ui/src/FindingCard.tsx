import type { FindingOut } from "@clausebook/api-client";
import { DiffView } from "./DiffView";

type Status = "in_playbook" | "fallback_proposed" | "outside_playbook";

// Derives a finding's display status from its matched and proposed positions.
function statusOf(finding: FindingOut): Status {
  if (!finding.proposed_position_id) return "in_playbook";
  if (!finding.matched_position_id) return "outside_playbook";
  return "fallback_proposed";
}

const LABEL_BY_STATUS: Record<Status, string> = {
  in_playbook: "In playbook",
  fallback_proposed: "Fallback proposed",
  outside_playbook: "Outside playbook",
};

const COLOR_BY_STATUS: Record<Status, string> = {
  in_playbook: "var(--cb-green)",
  fallback_proposed: "var(--cb-amber)",
  outside_playbook: "var(--cb-red)",
};

// The one finding card shared by the web app's review page and the add-in's task pane.
export function FindingCard({ finding, onDecide }: {
  finding: FindingOut;
  onDecide?: (decision: "accepted" | "rejected") => void;
}) {
  const status = statusOf(finding);
  const hunks = finding.redline.hunks ?? [];

  return (
    <div className="cb-panel" style={{ marginBottom: "1rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <span style={{ color: COLOR_BY_STATUS[status], fontWeight: 600 }}>{LABEL_BY_STATUS[status]}</span>
        <span className="cb-mono" style={{ fontSize: "0.8rem", color: "var(--cb-ink-muted)" }}>
          {finding.id.slice(0, 8)}
        </span>
      </div>
      {hunks.length > 0 && <DiffView hunks={hunks} />}
      {finding.evidence.reason && (
        <p style={{ color: "var(--cb-ink-muted)", fontSize: "0.9rem" }}>{finding.evidence.reason}</p>
      )}
      {onDecide && (
        <div style={{ display: "flex", gap: "0.75rem", marginTop: "0.75rem" }}>
          <button onClick={() => onDecide("accepted")}>Accept</button>
          <button onClick={() => onDecide("rejected")}>Reject</button>
        </div>
      )}
    </div>
  );
}
