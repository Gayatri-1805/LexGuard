"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { CheckEntry } from "@/lib/api";

interface Props {
  checks: CheckEntry[];
}

// Aggregate checks into daily buckets with avg trust_index
function bucketByDay(checks: CheckEntry[]) {
  const map = new Map<string, { sum: number; count: number }>();

  for (const c of checks) {
    const day = c.created_at.split("T")[0];
    const existing = map.get(day) ?? { sum: 0, count: 0 };
    map.set(day, { sum: existing.sum + c.trust_index, count: existing.count + 1 });
  }

  return Array.from(map.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, { sum, count }]) => ({
      date: new Date(date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      avg_trust: parseFloat((sum / count).toFixed(3)),
      checks: count,
    }));
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div
      style={{
        background: "rgba(14, 21, 33, 0.95)",
        border: "1px solid rgba(255,255,255,0.1)",
        borderRadius: 10,
        padding: "10px 14px",
        fontSize: 12,
      }}
    >
      <div style={{ color: "#94a3b8", marginBottom: 6 }}>{label}</div>
      <div style={{ color: "#f1f5f9", fontWeight: 700 }}>
        Avg Trust:{" "}
        <span style={{ color: trustColor(d.avg_trust) }}>
          {(d.avg_trust * 100).toFixed(1)}%
        </span>
      </div>
      <div style={{ color: "#94a3b8" }}>{d.checks} check{d.checks !== 1 ? "s" : ""}</div>
    </div>
  );
};

function trustColor(v: number) {
  if (v >= 0.7) return "#22d3a0";
  if (v >= 0.45) return "#f59e0b";
  return "#f43f5e";
}

export default function TrustTrendChart({ checks }: Props) {
  const data = bucketByDay(checks);

  if (data.length === 0) {
    return (
      <div className="loading-state" style={{ minHeight: 220 }}>
        No data yet
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
        <defs>
          <linearGradient id="trustGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="rgba(255,255,255,0.05)"
          vertical={false}
        />
        <XAxis
          dataKey="date"
          tick={{ fill: "#475569", fontSize: 11 }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          domain={[0, 1]}
          tick={{ fill: "#475569", fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
        />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine
          y={0.5}
          stroke="rgba(245,158,11,0.3)"
          strokeDasharray="4 4"
          label={{ value: "Threshold", fill: "#475569", fontSize: 10, position: "right" }}
        />
        <Line
          type="monotone"
          dataKey="avg_trust"
          stroke="#6366f1"
          strokeWidth={2.5}
          dot={{ fill: "#6366f1", strokeWidth: 0, r: 3 }}
          activeDot={{ r: 5, fill: "#818cf8" }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
