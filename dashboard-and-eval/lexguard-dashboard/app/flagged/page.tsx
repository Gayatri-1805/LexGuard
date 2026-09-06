"use client";

import { useEffect, useState } from "react";
import { api, CheckEntry } from "@/lib/api";
import FlaggedQueue from "@/components/FlaggedQueue";

const PAGE_SIZE = 20;

export default function FlaggedPage() {
  const [items, setItems] = useState<CheckEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .getFlagged(PAGE_SIZE, page * PAGE_SIZE)
      .then((data) => {
        setItems(data.flagged_checks);
        setTotal(data.total);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [page]);

  const flaggedCount = items.filter((i) => i.decision === "FLAGGED").length;
  const abstainCount = items.filter((i) => i.decision === "ABSTAIN").length;

  return (
    <>
      <div className="page-header">
        <h1>Flagged Checks</h1>
        <p>Hallucinations detected and abstentions requiring manual review</p>
      </div>

      {error && <div className="error-banner">⚠ {error}</div>}

      {/* Summary strip */}
      <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
        <div className="kpi-card" style={{ flex: 1, padding: "14px 18px" }}>
          <div className="kpi-label">Total Flagged</div>
          <div className="kpi-value" style={{ fontSize: 26 }}>{total.toLocaleString()}</div>
        </div>
        <div className="kpi-card" style={{ flex: 1, padding: "14px 18px" }}>
          <div className="kpi-label">Contradictions</div>
          <div className="kpi-value" style={{ fontSize: 26, color: "var(--accent-flagged)" }}>
            {flaggedCount}
          </div>
        </div>
        <div className="kpi-card" style={{ flex: 1, padding: "14px 18px" }}>
          <div className="kpi-label">Needs Review</div>
          <div className="kpi-value" style={{ fontSize: 26, color: "var(--accent-abstain)" }}>
            {abstainCount}
          </div>
        </div>
      </div>

      <div className="glass-card">
        <div className="card-title">Review Queue</div>
        <div className="card-subtitle">
          Ordered by most recent · Click a record to inspect claims
        </div>

        {loading ? (
          <div className="loading-state">
            <div className="spinner" />
            Loading flagged checks…
          </div>
        ) : (
          <FlaggedQueue
            items={items}
            total={total}
            page={page}
            pageSize={PAGE_SIZE}
            onPageChange={setPage}
          />
        )}
      </div>
    </>
  );
}
