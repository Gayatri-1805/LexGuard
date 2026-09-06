"use client";

import { CheckEntry } from "@/lib/api";

interface Props {
  checks: CheckEntry[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (p: number) => void;
}

function trustColor(v: number) {
  if (v >= 0.7) return "var(--accent-safe)";
  if (v >= 0.45) return "var(--accent-abstain)";
  return "var(--accent-flagged)";
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function ChecksTable({
  checks,
  total,
  page,
  pageSize,
  onPageChange,
}: Props) {
  const start = page * pageSize + 1;
  const end = Math.min((page + 1) * pageSize, total);
  const totalPages = Math.ceil(total / pageSize);

  return (
    <>
      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Request ID</th>
              <th>Decision</th>
              <th>Trust Score</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {checks.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>
                  No checks found
                </td>
              </tr>
            ) : (
              checks.map((c) => (
                <tr key={c.request_id}>
                  <td className="mono">{c.request_id.slice(0, 24)}…</td>
                  <td>
                    <span className={`decision-badge ${c.decision}`}>
                      {c.decision === "SAFE" && "✓ "}
                      {c.decision === "FLAGGED" && "⚑ "}
                      {c.decision === "ABSTAIN" && "~ "}
                      {c.decision}
                    </span>
                  </td>
                  <td>
                    <div className="trust-bar-wrap">
                      <div className="trust-bar-track">
                        <div
                          className="trust-bar-fill"
                          style={{
                            width: `${c.trust_index * 100}%`,
                            background: trustColor(c.trust_index),
                          }}
                        />
                      </div>
                      <span
                        className="trust-val"
                        style={{ color: trustColor(c.trust_index) }}
                      >
                        {(c.trust_index * 100).toFixed(0)}%
                      </span>
                    </div>
                  </td>
                  <td style={{ color: "var(--text-muted)", fontSize: 12 }}>
                    {formatDate(c.created_at)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="pagination">
        <span>
          {total > 0 ? `${start}–${end} of ${total.toLocaleString()} checks` : "No results"}
        </span>
        <div className="pagination-btns">
          <button
            className="btn"
            onClick={() => onPageChange(page - 1)}
            disabled={page === 0}
          >
            ← Prev
          </button>
          <button
            className="btn"
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages - 1}
          >
            Next →
          </button>
        </div>
      </div>
    </>
  );
}
