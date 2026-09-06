"use client";

import { CheckEntry } from "@/lib/api";

interface Props {
  items: CheckEntry[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (p: number) => void;
}

function formatDate(iso: string) {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function riskLevel(trust: number, decision: string) {
  if (decision === "FLAGGED" && trust < 0.2) return { label: "CRITICAL", color: "var(--accent-flagged)" };
  if (decision === "FLAGGED") return { label: "HIGH", color: "#fb7185" };
  if (decision === "ABSTAIN") return { label: "REVIEW", color: "var(--accent-abstain)" };
  return { label: "LOW", color: "var(--accent-safe)" };
}

export default function FlaggedQueue({ items, total, page, pageSize, onPageChange }: Props) {
  const totalPages = Math.ceil(total / pageSize);

  return (
    <>
      <div className="flagged-list">
        {items.length === 0 ? (
          <div className="loading-state" style={{ minHeight: 120 }}>
            🎉 No flagged checks — all clear!
          </div>
        ) : (
          items.map((item, idx) => {
            const risk = riskLevel(item.trust_index, item.decision);
            return (
              <div
                key={item.request_id}
                className={`flagged-item ${item.decision}`}
                style={{ animationDelay: `${idx * 40}ms` }}
              >
                <div>
                  <div className="flagged-id">{item.request_id.slice(0, 32)}…</div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 6 }}>
                    <span className={`decision-badge ${item.decision}`}>
                      {item.decision}
                    </span>
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      Trust: <strong style={{ color: risk.color }}>
                        {(item.trust_index * 100).toFixed(0)}%
                      </strong>
                    </span>
                  </div>
                  <div className="flagged-time">{formatDate(item.created_at)}</div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div
                    style={{
                      fontSize: 10,
                      fontWeight: 700,
                      letterSpacing: "0.8px",
                      textTransform: "uppercase",
                      color: risk.color,
                      border: `1px solid ${risk.color}33`,
                      borderRadius: 20,
                      padding: "3px 10px",
                      marginBottom: 8,
                    }}
                  >
                    {risk.label}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {totalPages > 1 && (
        <div className="pagination mt-4">
          <span>{total.toLocaleString()} flagged checks</span>
          <div className="pagination-btns">
            <button className="btn" onClick={() => onPageChange(page - 1)} disabled={page === 0}>
              ← Prev
            </button>
            <button className="btn" onClick={() => onPageChange(page + 1)} disabled={page >= totalPages - 1}>
              Next →
            </button>
          </div>
        </div>
      )}
    </>
  );
}
