import { useState } from "react";
import type { Position } from "@/api/client";

/** Ring sectors use actual weight angles; small holdings are explicitly grouped. */
export function AllocationChart({ positions }: { positions: Position[] }) {
  const [selected, setSelected] = useState<string | null>(null);
  const priced = positions
    .filter(
      (p) =>
        p.weight_pct !== null && Number.isFinite(Number(p.weight_pct)) && Number(p.weight_pct) > 0,
    )
    .map((p) => ({ label: p.ticker, weight: Number(p.weight_pct) }))
    .sort((a, b) => b.weight - a.weight);
  if (!priced.length)
    return (
      <p className="py-6 text-sm text-muted-foreground">
        Allocation is available once holdings are priced.
      </p>
    );
  const groups =
    priced.length > 6
      ? [
          ...priced.slice(0, 5),
          {
            label: "Other holdings",
            weight: priced.slice(5).reduce((sum, p) => sum + p.weight, 0),
          },
        ]
      : priced;
  const active = groups.find((p) => p.label === selected) ?? groups[0];
  const total = groups.reduce((sum, p) => sum + p.weight, 0);
  const point = (r: number, a: number) => `${150 + r * Math.cos(a)},${150 + r * Math.sin(a)}`;
  return (
    <div className="allocation-layout">
      <svg
        viewBox="0 0 300 300"
        className="mx-auto w-full max-w-[300px]"
        role="img"
        aria-label={`Portfolio allocation: ${groups.map((p) => `${p.label} ${p.weight.toFixed(1)}%`).join(", ")}`}
      >
        {groups.map((p, index) => {
          const start =
            -Math.PI / 2 +
            (groups.slice(0, index).reduce((sum, item) => sum + item.weight, 0) / total) *
              Math.PI *
              2;
          const end = start + (p.weight / total) * Math.PI * 2;
          const gap = groups.length === 1 ? 0 : Math.min(0.045, (end - start) * 0.15);
          const a = start + gap / 2,
            b = end - gap / 2,
            large = b - a > Math.PI ? 1 : 0;
          const fill = p.label === active.label ? "var(--accent)" : "var(--surface-2)";
          if (groups.length === 1)
            return (
              <circle
                key={p.label}
                cx="150"
                cy="150"
                r="88"
                fill="none"
                stroke={fill}
                strokeWidth="64"
              />
            );
          return (
            <path
              key={p.label}
              d={`M${point(120, a)} A120,120 0 ${large} 1 ${point(120, b)} L${point(56, b)} A56,56 0 ${large} 0 ${point(56, a)} Z`}
              fill={fill}
              stroke="var(--surface)"
              strokeWidth="5"
              strokeLinejoin="round"
            >
              <title>
                {p.label}: {p.weight.toFixed(1)}%
              </title>
            </path>
          );
        })}
        <text
          x="150"
          y="149"
          textAnchor="middle"
          fill="var(--foreground)"
          fontSize="26"
          fontFamily="IBM Plex Mono, monospace"
        >
          {active.weight.toFixed(1)}%
        </text>
        <text x="150" y="172" textAnchor="middle" fill="var(--muted-foreground)" fontSize="12">
          {active.label}
        </text>
      </svg>
      <div
        className="flex min-w-0 flex-col gap-1"
        role="group"
        aria-label="Highlight portfolio allocation"
      >
        {groups.map((p) => (
          <button
            key={p.label}
            type="button"
            aria-pressed={p.label === active.label}
            onClick={() => setSelected(p.label)}
            className="allocation-key"
          >
            <span className="flex items-center gap-2">
              <span
                aria-hidden="true"
                className={`h-2 w-2 rounded-full ${p.label === active.label ? "bg-accent" : "bg-faint"}`}
              />
              {p.label}
            </span>
            <span className="font-mono tabular-nums">{p.weight.toFixed(1)}%</span>
          </button>
        ))}
        <p className="mt-2 text-xs text-muted-foreground">
          Priced holdings · Weight by market value
          {priced.length > 6 ? " · Remaining holdings grouped" : ""}
        </p>
      </div>
    </div>
  );
}
