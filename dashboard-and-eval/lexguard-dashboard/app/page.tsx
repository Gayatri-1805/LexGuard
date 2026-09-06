import { api } from "@/lib/api";
import KpiCard from "@/components/KpiCard";
import TrustTrendChart from "@/components/TrustTrendChart";
import DecisionPieChart from "@/components/DecisionPieChart";

export const revalidate = 60;

export default async function OverviewPage() {
  let summary;
  let checks;
  let error: string | null = null;

  try {
    [summary, checks] = await Promise.all([
      api.getSummary(30),
      api.getChecks(200, 0),
    ]);
  } catch (e: any) {
    error = e?.message ?? "Failed to connect to API";
    summary = null;
    checks = null;
  }

  const hallucRate = summary
    ? ((summary.checks_flagged / Math.max(summary.total_checks, 1)) * 100).toFixed(1)
    : "—";

  return (
    <>
      <div className="page-header">
        <h1>Overview</h1>
        <p>
          Legal hallucination detection summary ·{" "}
          {summary?.date_range.from ?? "—"} → {summary?.date_range.to ?? "—"}
        </p>
      </div>

      {error && (
        <div className="error-banner">
          ⚠ API connection error: {error}. Check that the FastAPI server is running on{" "}
          <code>localhost:8000</code>.
        </div>
      )}

      {/* KPI Cards */}
      <div className="kpi-grid">
        <KpiCard
          label="Total Checks"
          value={summary?.total_checks ?? 0}
          sub="Last 30 days"
          badge={{ text: "30-day window", variant: "primary" }}
          accentColor="#6366f1"
        />
        <KpiCard
          label="Safe"
          value={summary?.checks_safe ?? 0}
          sub={`${summary ? ((summary.checks_safe / Math.max(summary.total_checks, 1)) * 100).toFixed(1) : 0}% of total`}
          badge={{ text: "Entailed", variant: "safe" }}
          accentColor="#22d3a0"
        />
        <KpiCard
          label="Flagged"
          value={summary?.checks_flagged ?? 0}
          sub={`${hallucRate}% hallucination rate`}
          badge={{ text: "Contradicted", variant: "flagged" }}
          accentColor="#f43f5e"
        />
        <KpiCard
          label="Abstained"
          value={summary?.checks_abstain ?? 0}
          sub="Insufficient evidence"
          badge={{ text: "Needs review", variant: "abstain" }}
          accentColor="#f59e0b"
        />
        <KpiCard
          label="Avg Trust Score"
          value={summary?.avg_trust_index ?? 0}
          prefix=""
          decimals={2}
          sub="0 = risky · 1 = safe"
          accentColor="#6366f1"
        />
      </div>

      {/* Charts */}
      <div className="chart-grid">
        <div className="glass-card">
          <div className="card-title">Trust Score Trend</div>
          <div className="card-subtitle">Daily average trust index over last 30 days</div>
          {checks ? (
            <TrustTrendChart checks={checks.checks} />
          ) : (
            <div className="loading-state" style={{ minHeight: 220 }}>
              <div className="spinner" />
              Loading…
            </div>
          )}
        </div>

        <div className="glass-card">
          <div className="card-title">Decision Breakdown</div>
          <div className="card-subtitle">Safe / Flagged / Abstain distribution</div>
          {summary ? (
            <DecisionPieChart summary={summary} />
          ) : (
            <div className="loading-state" style={{ minHeight: 220 }}>
              <div className="spinner" />
              Loading…
            </div>
          )}
        </div>
      </div>

      {/* Date range info */}
      {summary && (
        <div className="glass-card" style={{ display: "flex", gap: 32, flexWrap: "wrap" }}>
          <div>
            <div className="kpi-label">Window Start</div>
            <div style={{ color: "var(--text-secondary)", fontSize: 14, fontWeight: 600 }}>
              {summary.date_range.from}
            </div>
          </div>
          <div>
            <div className="kpi-label">Window End</div>
            <div style={{ color: "var(--text-secondary)", fontSize: 14, fontWeight: 600 }}>
              {summary.date_range.to}
            </div>
          </div>
          <div>
            <div className="kpi-label">Hallucination Rate</div>
            <div style={{ color: "var(--accent-flagged)", fontSize: 14, fontWeight: 700 }}>
              {hallucRate}%
            </div>
          </div>
          <div>
            <div className="kpi-label">Average Trust Index</div>
            <div style={{ color: "var(--accent-safe)", fontSize: 14, fontWeight: 700 }}>
              {summary.avg_trust_index}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
