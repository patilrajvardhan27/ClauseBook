// Thin fetch wrapper: one function per endpoint, no magic. Both apps/web
// and apps/addin import this instead of calling fetch directly, so a
// header or error-handling change happens once.
import type { DealContext, FindingOut, PlaybookOut, PreviewResponse, ReviewOut } from "./types";

export interface ClausebookClientConfig {
  baseUrl: string;
}

export function createClient({ baseUrl }: ClausebookClientConfig) {
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
    listPlaybooks: () => request<PlaybookOut[]>("/v1/playbooks"),

    uploadDocument: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      const response = await fetch(`${baseUrl}/v1/documents`, { method: "POST", body: form });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      return response.json() as Promise<{ id: string; title: string; pages: number; sha256: string; uploaded_at: string }>;
    },

    search: (query: string, clauseType?: string) => {
      const params = new URLSearchParams({ q: query, ...(clauseType ? { clause_type: clauseType } : {}) });
      return request<{ query: string; results: Array<{ precedent_id: string; score: number }> }>(
        `/v1/search?${params.toString()}`,
      );
    },

    startReview: (documentId: string, playbookId: string, dealContext: DealContext = {}) =>
      request<ReviewOut>("/v1/reviews", {
        method: "POST",
        body: JSON.stringify({ document_id: documentId, playbook_id: playbookId, deal_context: dealContext }),
      }),

    getReview: (reviewId: string) => request<ReviewOut>(`/v1/reviews/${reviewId}`),

    getFinding: (findingId: string) => request<FindingOut>(`/v1/findings/${findingId}`),

    decideFinding: (findingId: string, decision: "accepted" | "rejected" | "edited", reason?: string) =>
      request<FindingOut>(`/v1/findings/${findingId}`, {
        method: "PATCH",
        body: JSON.stringify({ decision, reason }),
      }),

    previewPlacement: (playbookId: string, clauseText: string, clauseTypeId: string, dealContext: DealContext = {}) =>
      request<PreviewResponse>(`/v1/playbooks/${playbookId}/preview`, {
        method: "POST",
        body: JSON.stringify({ clause_text: clauseText, clause_type_id: clauseTypeId, deal_context: dealContext }),
      }),

    openReviewEventStream: (reviewId: string, baseUrlOverride?: string) =>
      new EventSource(`${baseUrlOverride ?? baseUrl}/v1/reviews/${reviewId}/events`),

    marketPercentiles: (clauseType: string) => request<Record<string, unknown>>(`/v1/analytics/market/${clauseType}`),

    overrideRates: () => request<{ total_decided: number; rejected: number; override_rate: number }>(
      "/v1/analytics/overrides",
    ),
  };
}

export type ClausebookClient = ReturnType<typeof createClient>;
export * from "./types";
