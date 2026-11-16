// Thin fetch wrapper shared by apps/web and apps/addin, one function per endpoint.
import type { DealContext, FindingOut, PlaybookOut, PreviewResponse, ReviewOut } from "./types";

export interface ClausebookClientConfig {
  baseUrl: string;
}

// Builds the typed client every page and the task pane call against the API.
export function createClient({ baseUrl }: ClausebookClientConfig) {
  // Fetches JSON from the API, throwing on a non-OK response.
  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${baseUrl}${path}`, {
      headers: { "Content-Type": "application/json", ...init?.headers },
      ...init,
    });
    if (!response.ok) {
      const body = await response.text();
      throw new Error(`${response.status} ${response.statusText}: ${body}`);
    }
    return response.json() as Promise<T>;
  }

  return {
    // Lists every playbook.
    listPlaybooks: () => request<PlaybookOut[]>("/v1/playbooks"),

    // Uploads a document file.
    uploadDocument: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      const response = await fetch(`${baseUrl}/v1/documents`, { method: "POST", body: form });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      return response.json() as Promise<{ id: string; title: string; pages: number; sha256: string; uploaded_at: string }>;
    },

    // Runs a hybrid precedent search, optionally filtered by clause type.
    search: (query: string, clauseType?: string) => {
      const params = new URLSearchParams({ q: query, ...(clauseType ? { clause_type: clauseType } : {}) });
      return request<{ query: string; results: Array<{ precedent_id: string; score: number }> }>(
        `/v1/search?${params.toString()}`,
      );
    },

    // Starts a review for a document against a playbook.
    startReview: (documentId: string, playbookId: string, dealContext: DealContext = {}) =>
      request<ReviewOut>("/v1/reviews", {
        method: "POST",
        body: JSON.stringify({ document_id: documentId, playbook_id: playbookId, deal_context: dealContext }),
      }),

    // Fetches one review's current status.
    getReview: (reviewId: string) => request<ReviewOut>(`/v1/reviews/${reviewId}`),

    // Fetches one finding.
    getFinding: (findingId: string) => request<FindingOut>(`/v1/findings/${findingId}`),

    // Records an accept, reject or edit decision on a finding.
    decideFinding: (findingId: string, decision: "accepted" | "rejected" | "edited", reason?: string) =>
      request<FindingOut>(`/v1/findings/${findingId}`, {
        method: "PATCH",
        body: JSON.stringify({ decision, reason }),
      }),

    // Places a pasted clause against a playbook with no review behind it.
    previewPlacement: (playbookId: string, clauseText: string, clauseTypeId: string, dealContext: DealContext = {}) =>
      request<PreviewResponse>(`/v1/playbooks/${playbookId}/preview`, {
        method: "POST",
        body: JSON.stringify({ clause_text: clauseText, clause_type_id: clauseTypeId, deal_context: dealContext }),
      }),

    // Opens the SSE stream of a review's events.
    openReviewEventStream: (reviewId: string, baseUrlOverride?: string) =>
      new EventSource(`${baseUrlOverride ?? baseUrl}/v1/reviews/${reviewId}/events`),

    // Returns percentile stats for one clause type's attributes.
    marketPercentiles: (clauseType: string) => request<Record<string, unknown>>(`/v1/analytics/market/${clauseType}`),

    // Returns how often reviewers reject a proposed finding.
    overrideRates: () => request<{ total_decided: number; rejected: number; override_rate: number }>(
      "/v1/analytics/overrides",
    ),
  };
}

export type ClausebookClient = ReturnType<typeof createClient>;
export * from "./types";
