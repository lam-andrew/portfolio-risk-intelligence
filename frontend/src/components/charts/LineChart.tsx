import { useId, useState } from "react";
import { useChartWidth } from "./useChartWidth";

export interface ChartPoint {
  date: string;
  value: number;
}
interface Props {
  points: ChartPoint[];
  label: string;
  unit: string;
  formatValue: (value: number) => string;
  color?: string;
  underwater?: boolean;
}

/** All observations form the line; sparse dots preserve readability on long histories. */
export function LineChart({
  points,
  label,
  unit,
  formatValue,
  color = "var(--accent)",
  underwater = false,
}: Props) {
  const { ref, width } = useChartWidth();
  const id = useId();
  const [inspected, setInspected] = useState<number | null>(null);
  const valid = points.filter((p) => Number.isFinite(p.value));
  if (!valid.length)
    return <p className="py-8 text-sm text-muted-foreground">No price history available.</p>;
  const selected = Math.min(inspected ?? valid.length - 1, valid.length - 1);
  const active = valid[selected];
  const values = valid.map((p) => p.value);
  const min = Math.min(...values),
    max = Math.max(...values);
  const trough = values.indexOf(min);
  const pad = Math.max((max - min) * 0.12, Math.abs(max) * 0.02, underwater ? 1 : 0.01);
  const low = underwater ? Math.min(min, -1) * 1.12 : min - pad;
  const high = underwater ? 0 : max + pad;
  const left = 66,
    right = Math.max(left + 40, width - 14),
    top = 18,
    bottom = 196;
  const x = (i: number) => left + (i / Math.max(valid.length - 1, 1)) * (right - left);
  const y = (v: number) => top + ((high - v) / (high - low)) * (bottom - top);
  const line = valid.map((p, i) => `${i ? "L" : "M"}${x(i)},${y(p.value)}`).join(" ");
  const step = Math.max(1, Math.ceil(valid.length / Math.max(4, Math.floor(width / 35))));
  const ticks = [
    ...new Set(
      width < 440
        ? [0, valid.length - 1]
        : [0, Math.floor((valid.length - 1) / 2), valid.length - 1],
    ),
  ];
  return (
    <div ref={ref} className="orbit-chart">
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2 text-xs">
        <span className="text-muted-foreground">{unit}</span>
        <output className="font-mono tabular-nums" aria-live="polite">
          {active.date} · {formatValue(active.value)}
        </output>
      </div>
      <svg
        viewBox={`0 0 ${width} 230`}
        className="w-full"
        style={{ height: 230 }}
        role="img"
        aria-label={`${label}. ${valid.length} observations, ${valid[0].date} to ${valid[valid.length - 1].date}.`}
        onPointerMove={(e) => {
          const box = e.currentTarget.getBoundingClientRect();
          setInspected(
            Math.max(
              0,
              Math.min(
                valid.length - 1,
                Math.round(
                  ((((e.clientX - box.left) / box.width) * width - left) / (right - left)) *
                    (valid.length - 1),
                ),
              ),
            ),
          );
        }}
      >
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={color} stopOpacity=".04" />
            <stop offset="1" stopColor={color} stopOpacity=".16" />
          </linearGradient>
        </defs>
        {[0, 1, 2, 3].map((i) => {
          const v = low + ((high - low) * i) / 3;
          return (
            <g key={i}>
              <line
                x1={left}
                x2={right}
                y1={y(v)}
                y2={y(v)}
                stroke="var(--border)"
                strokeDasharray={(underwater ? i === 3 : i === 0) ? "2 6" : undefined}
              />
              <text x={left - 8} y={y(v) + 4} textAnchor="end" className="chart-axis">
                {underwater
                  ? `${v.toFixed(1)}%`
                  : new Intl.NumberFormat(undefined, {
                      notation: "compact",
                      maximumFractionDigits: 1,
                    }).format(v)}
              </text>
            </g>
          );
        })}
        {underwater && (
          <path
            d={`${line} L${x(valid.length - 1)},${y(0)} L${x(0)},${y(0)} Z`}
            fill={`url(#${id})`}
          />
        )}
        <path d={line} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" />
        {valid.map(
          (p, i) =>
            (i % step === 0 || i === valid.length - 1 || i === trough) && (
              <g key={i}>
                <circle cx={x(i)} cy={y(p.value)} r="7" fill={color} opacity=".14" />
                <circle cx={x(i)} cy={y(p.value)} r="3" fill={color} />
              </g>
            ),
        )}
        <line
          x1={x(selected)}
          x2={x(selected)}
          y1={top}
          y2={bottom}
          stroke="var(--muted-foreground)"
          strokeDasharray="2 5"
          opacity=".5"
        />
        <circle
          cx={x(selected)}
          cy={y(active.value)}
          r="5"
          fill={color}
          stroke="var(--surface)"
          strokeWidth="2"
        />
        {ticks.map((i) => (
          <text
            key={i}
            x={x(i)}
            y="218"
            textAnchor={i === 0 ? "start" : i === valid.length - 1 ? "end" : "middle"}
            className="chart-axis"
          >
            {valid[i].date}
          </text>
        ))}
      </svg>
      {valid.length > 1 && (
        <label className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
          Inspect date
          <input
            aria-label={`Inspect ${label}`}
            type="range"
            min="0"
            max={valid.length - 1}
            value={selected}
            onChange={(e) => setInspected(Number(e.target.value))}
            className="min-w-0 flex-1 accent-accent"
          />
        </label>
      )}
    </div>
  );
}
