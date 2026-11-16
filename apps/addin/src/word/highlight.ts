/**
 * Colors a located range by finding status, using range.font.highlightColor
 * as the plan specifies, so a lawyer can see at a glance which clauses need
 * attention without opening the task pane's detail view for each one.
 */
export type FindingStatus = "in_playbook" | "fallback_proposed" | "outside_playbook";

const HIGHLIGHT_BY_STATUS: Record<FindingStatus, string> = {
  in_playbook: "#C6E6D9", // light green
  fallback_proposed: "#F6DFB2", // light amber
  outside_playbook: "#F2C6C2", // light red
};

export function highlightRange(range: Word.Range, status: FindingStatus): void {
  range.font.highlightColor = HIGHLIGHT_BY_STATUS[status];
}
