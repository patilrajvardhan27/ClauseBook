// Mirrors services/api/schemas.py. Hand-kept in this slice; a generated
// client from contracts/openapi/openapi.json replaces this file once the
// OpenAPI generator step is wired into the build.
export interface DealContext {
  party_role?: string;
  deal_size_band?: string;
  counterparty_type?: string;
}

export interface ReviewOut {
  id: string;
  document_id: string;
  playbook_id: string;
  status: "queued" | "running" | "done" | "error";
  started_at: string | null;
  finished_at: string | null;
}

export interface FindingOut {
  id: string;
  segment_id: string;
  clause_type_id: string | null;
  confidence: number;
  attrs: Record<string, unknown>;
  matched_position_id: string | null;
  proposed_position_id: string | null;
  redline: { hunks?: DiffHunk[]; edit_ratio?: number };
  evidence: { precedent_hits?: PrecedentHit[]; reason?: string; better_attributes?: string[] };
  decision: "accepted" | "rejected" | "edited" | null;
}

export interface DiffHunk {
  op: "equal" | "insert" | "delete";
  text: string;
}

export interface PrecedentHit {
  precedent_id: string;
  score: number;
}

export interface PlaybookOut {
  id: string;
  firm_id: string;
  name: string;
  side: string;
  version: number;
  published_at: string | null;
}

export interface PreviewResponse {
  attrs: Record<string, unknown>;
  matched_position_id: string | null;
  proposed_position_id: string | null;
  outside_playbook: boolean;
  reason: string;
}
