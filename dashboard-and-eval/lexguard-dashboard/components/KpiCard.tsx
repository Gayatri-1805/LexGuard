"use client";

import { useEffect, useRef, useState } from "react";

interface KpiCardProps {
  label: string;
  value: number | string;
  sub?: string;
  badge?: { text: string; variant: "safe" | "flagged" | "abstain" | "primary" };
  accentColor?: string;
  prefix?: string;
  decimals?: number;
  animate?: boolean;
}

function useCountUp(target: number, duration = 900, animate = true) {
  const [val, setVal] = useState(0);
  const raf = useRef<number>(0);

  useEffect(() => {
    if (!animate) { setVal(target); return; }
    const start = performance.now();
    const tick = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      // easeOutExpo
      const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      setVal(eased * target);
      if (progress < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [target, duration, animate]);

  return val;
}

export default function KpiCard({
  label,
  value,
  sub,
  badge,
  accentColor = "#6366f1",
  prefix = "",
  decimals = 0,
  animate = true,
}: KpiCardProps) {
  const numericValue = typeof value === "number" ? value : parseFloat(String(value));
  const animated = useCountUp(isNaN(numericValue) ? 0 : numericValue, 900, animate);

  const displayVal = isNaN(numericValue)
    ? value
    : `${prefix}${animated.toFixed(decimals)}`;

  return (
    <div
      className="kpi-card"
      style={{ "--card-accent-color": accentColor } as React.CSSProperties}
    >
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{displayVal}</div>
      {sub && <div className="kpi-sub">{sub}</div>}
      {badge && (
        <div className={`kpi-badge ${badge.variant}`}>{badge.text}</div>
      )}
    </div>
  );
}
