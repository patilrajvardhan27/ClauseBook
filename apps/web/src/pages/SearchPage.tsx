import { useState } from "react";
import { createClient } from "@clausebook/api-client";

const client = createClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? "" });

// Hybrid precedent search (BM25 + kNN, fused and reranked server-side);
// this page only shapes the query and renders ranked hits.
export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Array<{ precedent_id: string; score: number }>>([]);

  async function handleSearch(event: React.FormEvent) {
    event.preventDefault();
    const response = await client.search(query);
    setResults(response.results);
  }

  return (
    <section>
      <h1>Search</h1>
      <form onSubmit={handleSearch} style={{ display: "flex", gap: "0.5rem" }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search precedent, e.g. uncapped IP indemnity"
          style={{ flex: 1, padding: "0.5rem" }}
        />
        <button type="submit">Search</button>
      </form>
      {results.map((hit) => (
        <div key={hit.precedent_id} className="cb-panel" style={{ marginTop: "0.75rem" }}>
          <span className="cb-mono">{hit.precedent_id}</span>
          <span style={{ float: "right", color: "var(--cb-ink-muted)" }}>score {hit.score.toFixed(3)}</span>
        </div>
      ))}
    </section>
  );
}
