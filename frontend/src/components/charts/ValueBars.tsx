import { useId, useState } from "react";
import { useChartWidth } from "./useChartWidth";

interface Props {
  items: { label: string; value: number }[];
  label: string;
  formatValue: (v: number) => string;
  unit: string;
}
export function ValueBars({ items, label, formatValue, unit }: Props) {
  const { ref, width } = useChartWidth();
  const id = useId();
  const [selected, setSelected] = useState<string | null>(null);
  const values = items.filter((p) => Number.isFinite(p.value) && p.value >= 0);
  if (!values.length) return null;
  const active = values.find((p) => p.label === selected) ?? values[0];
  const max = Math.max(...values.map((p) => p.value), 1);
  const left = 50,
    right = width - 8,
    top = 25,
    bottom = 205;
  const slot = (right - left) / values.length;
  const bar = Math.min(slot * 0.66, 65);
  return (
    <div ref={ref} className="orbit-chart">
      <svg
        viewBox={`0 0 ${width} 240`}
        className="w-full"
        style={{ height: 240 }}
        role="img"
        aria-label={`${label}. ${values.map((p) => `${p.label}: ${formatValue(p.value)}`).join(", ")}`}
      >
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="var(--accent)" />
            <stop offset="1" stopColor="var(--accent)" stopOpacity=".15" />
          </linearGradient>
        </defs>
        {[0, 0.5, 1].map((f) => (
          <g key={f}>
            <line
              x1={left}
              x2={right}
              y1={bottom - f * (bottom - top)}
              y2={bottom - f * (bottom - top)}
              stroke="var(--border)"
              strokeDasharray={f === 0 ? "2 6" : undefined}
            />
            <text
              x={left - 7}
              y={bottom - f * (bottom - top) + 4}
              textAnchor="end"
              className="chart-axis"
            >
              {new Intl.NumberFormat(undefined, {
                notation: "compact",
                maximumFractionDigits: 1,
              }).format(f * max)}
            </text>
          </g>
        ))}
        <text x="0" y="12" className="chart-axis">
          {unit}
        </text>
        {values.map((p, i) => {
          const height = (p.value / max) * (bottom - top),
            x = left + i * slot + (slot - bar) / 2,
            y = bottom - height;
          return (
            <g key={p.label}>
              <rect
                data-bar={p.label}
                x={x}
                y={y}
                width={bar}
                height={height}
                rx="7"
                fill={p.label === active.label ? `url(#${id})` : "var(--surface-2)"}
                className="chart-bar"
              >
                <title>
                  {p.label}: {formatValue(p.value)}
                </title>
              </rect>
              {height > 8 && (
                <line
                  x1={x + 5}
                  x2={x + bar - 5}
                  y1={y + 5}
                  y2={y + 5}
                  stroke={p.label === active.label ? "var(--accent)" : "var(--muted-foreground)"}
                  strokeWidth="1.5"
                />
              )}
              <text x={x + bar / 2} y="227" textAnchor="middle" className="chart-axis">
                {p.label.length > Math.floor(slot / 7)
                  ? `${p.label.slice(0, Math.max(2, Math.floor(slot / 7) - 1))}…`
                  : p.label}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="flex flex-wrap gap-2" role="group" aria-label={`Highlight ${label}`}>
        {values.map((p) => (
          <button
            type="button"
            key={p.label}
            aria-pressed={p.label === active.label}
            onClick={() => setSelected(p.label)}
            className="chart-choice"
          >
            {p.label}
          </button>
        ))}
      </div>
      <p className="mt-3 text-xs text-muted-foreground" aria-live="polite">
        {active.label} ·{" "}
        <span className="font-mono text-foreground">{formatValue(active.value)}</span>
      </p>
    </div>
  );
}
