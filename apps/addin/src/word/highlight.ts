// Colors a located range by finding status, so a lawyer sees at a glance what needs attention.
export type FindingStatus = "in_playbook" | "fallback_proposed" | "outside_playbook";

const HIGHLIGHT_BY_STATUS: Record<FindingStatus, string> = {
  in_playbook: "#C6E6D9", // light green
  fallback_proposed: "#F6DFB2", // light amber
  outside_playbook: "#F2C6C2", // light red
};

// Sets a range's highlight color for a finding's status.
export function highlightRange(range: Word.Range, status: FindingStatus): void {
  range.font.highlightColor = HIGHLIGHT_BY_STATUS[status];
}
