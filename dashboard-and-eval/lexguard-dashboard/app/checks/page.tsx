"use client";

import { useEffect, useState } from "react";
import { api, CheckEntry } from "@/lib/api";
import ChecksTable from "@/components/ChecksTable";

const PAGE_SIZE = 25;

export default function ChecksPage() {
  const [checks, setChecks] = useState<CheckEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .getChecks(PAGE_SIZE, page * PAGE_SIZE)
      .then((data) => {
        setChecks(data.checks);
        setTotal(data.total);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [page]);

  return (
    <>
      <div className="page-header">
        <h1>All Checks</h1>
        <p>Paginated log of every hallucination detection request</p>
      </div>

      {error && <div className="error-banner">⚠ {error}</div>}

      <div className="glass-card">
        <div className="flex-between section-gap">
          <div>
            <div className="card-title">Check Log</div>
            <div className="card-subtitle">{total.toLocaleString()} total checks</div>
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Auto-refreshes every 60s
          </div>
        </div>

        {loading ? (
          <div className="loading-state">
            <div className="spinner" />
            Loading checks…
          </div>
        ) : (
          <ChecksTable
            checks={checks}
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
