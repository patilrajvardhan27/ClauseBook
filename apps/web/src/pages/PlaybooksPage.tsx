import { useEffect, useState } from "react";
import { createClient, type PlaybookOut } from "@clausebook/api-client";
import { Skeleton } from "@clausebook/ui";

const client = createClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? "" });

// The ladder editor itself (ordered positions, conditions as form rows,
// preview box) is the heaviest remaining UI piece; this page lists
// playbooks and marks which ones are sample data, per the plan's rule
// that synthetic playbooks must say so on screen.
export default function PlaybooksPage() {
  const [playbooks, setPlaybooks] = useState<PlaybookOut[] | null>(null);

  useEffect(() => {
    client.listPlaybooks().then(setPlaybooks).catch(() => setPlaybooks([]));
  }, []);

  return (
    <section>
      <h1>Playbooks</h1>
      {!playbooks ? (
        <Skeleton height={120} />
      ) : (
        playbooks.map((playbook) => (
          <div key={playbook.id} className="cb-panel" style={{ marginBottom: "1rem" }}>
            <h2 style={{ margin: 0 }}>{playbook.name}</h2>
            {playbook.name.toLowerCase().startsWith("sample") && (
              <p style={{ color: "var(--cb-amber)", fontSize: "0.85rem" }}>
                Sample playbook, built from public drafting guidance. Not any real firm's guidance.
              </p>
            )}
            <p className="cb-mono" style={{ fontSize: "0.8rem", color: "var(--cb-ink-muted)" }}>
              {playbook.side} side &middot; version {playbook.version}
            </p>
          </div>
        ))
      )}
    </section>
  );
}
