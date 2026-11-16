import { useEffect, useState } from "react";
import { createClient } from "@clausebook/api-client";
import { Skeleton } from "@clausebook/ui";

const client = createClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? "" });

// Market percentiles and override rates; co-occurrence rules (Apriori)
// are a should-ship item per the plan and are not wired into this page yet.
export default function AnalyticsPage() {
  const [overrides, setOverrides] = useState<{ total_decided: number; rejected: number; override_rate: number } | null>(null);

  useEffect(() => {
    client.overrideRates().then(setOverrides).catch(() => setOverrides(null));
  }, []);

  return (
    <section>
      <h1>Analytics</h1>
      <div className="cb-panel">
        <h2 style={{ marginTop: 0 }}>Override rate</h2>
        {overrides === null ? (
          <Skeleton height={24} width={200} />
        ) : (
          <p>
            {overrides.rejected} of {overrides.total_decided} decided findings were rejected
            ({(overrides.override_rate * 100).toFixed(1)}%).
          </p>
        )}
      </div>
    </section>
  );
}
