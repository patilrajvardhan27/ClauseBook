// Mirrors services/api/schemas.py; hand-kept until a generated client replaces it.

// The deal context a placement is evaluated against.
export interface DealContext {
  party_role?: string;
  deal_size_band?: string;
  counterparty_type?: string;
}

// A review run.
export interface ReviewOut {
  id: string;
  document_id: string;
  playbook_id: string;
  status: "queued" | "running" | "done" | "error";
  started_at: string | null;
  finished_at: string | null;
}

// One clause's finding.
export interface FindingOut {
  id: string;
  segment_id: string;
  clause_type_id: string | null;
  confidence: number;
  attrs: Record<string, unknown>;
  matched_position_id: string | null;
  proposed_position_id: string | null;
  redline: { hunks?: DiffHunk[]; edit_ratio?: number };
  evidence: {
    precedent_hits?: PrecedentHit[];
    reason?: string;
    better_attributes?: string[];
    segment_text?: string;
  };
  decision: "accepted" | "rejected" | "edited" | null;
}

// One run of equal, inserted or deleted text in a word-level diff.
export interface DiffHunk {
  op: "equal" | "insert" | "delete";
  text: string;
}

// One retrieved precedent and its fused rank score.
export interface PrecedentHit {
  precedent_id: string;
  score: number;
}

// A playbook.
export interface PlaybookOut {
  id: string;
  firm_id: string;
  name: string;
  side: string;
  version: number;
  published_at: string | null;
}

// What the placement engine decided for a previewed clause.
export interface PreviewResponse {
  attrs: Record<string, unknown>;
  matched_position_id: string | null;
  proposed_position_id: string | null;
  outside_playbook: boolean;
  reason: string;
}
