"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { SummaryData } from "@/lib/api";

interface Props {
  summary: SummaryData;
}

const COLORS = {
  SAFE: "#22d3a0",
  FLAGGED: "#f43f5e",
  ABSTAIN: "#f59e0b",
};

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const { name, value, payload: p } = payload[0];
  const pct = ((value / p.total) * 100).toFixed(1);
  return (
    <div
      style={{
        background: "rgba(14,21,33,0.95)",
        border: "1px solid rgba(255,255,255,0.1)",
        borderRadius: 10,
        padding: "10px 14px",
        fontSize: 12,
      }}
    >
      <div style={{ color: COLORS[name as keyof typeof COLORS], fontWeight: 700 }}>
        {name}
      </div>
      <div style={{ color: "#f1f5f9" }}>
        {value.toLocaleString()} checks ({pct}%)
      </div>
    </div>
  );
};

const renderCustomLabel = ({
  cx, cy, midAngle, innerRadius, outerRadius, percent,
}: any) => {
  if (percent < 0.05) return null;
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  return (
    <text
      x={x} y={y}
      fill="#f1f5f9"
      textAnchor="middle"
      dominantBaseline="central"
      fontSize={12}
      fontWeight={700}
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

export default function DecisionPieChart({ summary }: Props) {
  const total = summary.total_checks || 1;
  const data = [
    { name: "SAFE", value: summary.checks_safe, total },
    { name: "FLAGGED", value: summary.checks_flagged, total },
    { name: "ABSTAIN", value: summary.checks_abstain, total },
  ].filter((d) => d.value > 0);

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={55}
          outerRadius={88}
          paddingAngle={3}
          dataKey="value"
          labelLine={false}
          label={renderCustomLabel}
          animationBegin={100}
          animationDuration={900}
        >
          {data.map((entry) => (
            <Cell
              key={entry.name}
              fill={COLORS[entry.name as keyof typeof COLORS]}
              opacity={0.85}
            />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(val) => (
            <span style={{ color: "#94a3b8", fontSize: 12 }}>{val}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
