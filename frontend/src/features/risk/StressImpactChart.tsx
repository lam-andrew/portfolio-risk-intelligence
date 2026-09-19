import { useId } from "react";

import type { PortfolioStress } from "@/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/features/holdings/format";

/** A value bridge, not a time series. Coordinates only scale values returned by the API. */
export function StressImpactChart({ data }: { data: PortfolioStress }) {
  const patternId = `stress-loss-${useId().replace(/:/g, "")}`;
  const baseline = Number(data.baseline_value);
  const loss = Number(data.loss);
  const after = Number(data.stressed_value);
  if (
    data.status !== "ready" ||
    data.baseline_value === null ||
    data.loss === null ||
    data.stressed_value === null ||
    !Number.isFinite(baseline) ||
    baseline <= 0 ||
    !Number.isFinite(loss) ||
    !Number.isFinite(after) ||
    loss < 0 ||
    after < 0
  )
    return null;

  const lossHeight = Math.min(loss / baseline, 1) * 180;
  const afterHeight = Math.min(after / baseline, 1) * 180;
  const afterTop = 200 - afterHeight;
  const largest = [...data.positions].sort((a, b) => Number(b.loss) - Number(a.loss)).slice(0, 5);
  const maxLoss = Math.max(0, ...largest.map((p) => Number(p.loss)));

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>From baseline to stressed value</CardTitle>
          <CardDescription>
            The red step is the estimated loss. This compares values, not movement over time.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <figure aria-label="Portfolio stress impact">
            <div className="grid grid-cols-[38px_1fr] gap-2">
              <div
                aria-hidden="true"
                className="relative h-[220px] text-right font-mono text-[10px] text-muted-foreground"
              >
                {[
                  [20, "100%"],
                  [110, "50%"],
                  [200, "0%"],
                ].map(([top, label]) => (
                  <span key={label} className="absolute right-0 -translate-y-1/2" style={{ top }}>
                    {label}
                  </span>
                ))}
              </div>
              <svg
                viewBox="0 0 600 220"
                preserveAspectRatio="none"
                className="h-[220px] w-full"
                role="img"
                aria-label={`Starting value ${formatCurrency(data.baseline_value)}, estimated loss ${formatCurrency(data.loss)}, remaining value ${formatCurrency(data.stressed_value)}. Scale starts at zero.`}
              >
                <defs>
                  <pattern
                    id={patternId}
                    width="8"
                    height="8"
                    patternUnits="userSpaceOnUse"
                    patternTransform="rotate(45)"
                  >
                    <rect width="8" height="8" fill="var(--down)" fillOpacity="0.12" />
                    <line
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="8"
                      stroke="var(--down)"
                      strokeOpacity="0.65"
                      strokeWidth="2"
                    />
                  </pattern>
                </defs>
                {[20, 110, 200].map((y) => (
                  <line
                    key={y}
                    x1="0"
                    x2="600"
                    y1={y}
                    y2={y}
                    stroke="var(--border)"
                    strokeDasharray={y === 200 ? undefined : "4 5"}
                  />
                ))}
                <rect
                  x="30"
                  y="20"
                  width="140"
                  height="180"
                  rx="3"
                  fill="var(--accent)"
                  fillOpacity="0.45"
                >
                  <title>Baseline value</title>
                </rect>
                <line
                  x1="170"
                  x2="230"
                  y1="20"
                  y2="20"
                  stroke="var(--muted-foreground)"
                  strokeDasharray="4 4"
                />
                <rect
                  x="230"
                  y="20"
                  width="140"
                  height={lossHeight}
                  fill={`url(#${patternId})`}
                  stroke="var(--down)"
                >
                  <title>Estimated loss step</title>
                </rect>
                <line
                  x1="370"
                  x2="430"
                  y1={afterTop}
                  y2={afterTop}
                  stroke="var(--muted-foreground)"
                  strokeDasharray="4 4"
                />
                <rect
                  x="430"
                  y={afterTop}
                  width="140"
                  height={afterHeight}
                  rx="3"
                  fill="var(--accent)"
                >
                  <title>Value after scenario</title>
                </rect>
              </svg>
              <span aria-hidden="true" />
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                {[
                  ["Baseline", formatCurrency(data.baseline_value)],
                  ["Loss", `−${formatCurrency(data.loss)}`],
                  ["After scenario", formatCurrency(data.stressed_value)],
                ].map(([label, value]) => (
                  <div key={label} className="flex min-w-0 flex-col gap-1">
                    <span className="text-muted-foreground">{label}</span>
                    <span className="break-words font-mono font-medium tabular-nums">{value}</span>
                  </div>
                ))}
              </div>
            </div>
            <figcaption className="mt-4 text-xs text-muted-foreground">
              Height shows the share of baseline value. The hatched step removes the loss from the
              starting amount.
            </figcaption>
          </figure>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>What contributes most to the loss?</CardTitle>
          <CardDescription>
            {data.positions.length > 5
              ? "The five largest dollar losses; every holding is listed below."
              : "Holdings ranked by estimated dollar loss."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ol aria-label="Largest loss contributions" className="flex flex-col gap-4">
            {largest.map((p) => (
              <li key={p.ticker}>
                <div className="mb-1.5 flex items-baseline justify-between gap-3 text-sm">
                  <span className="font-mono font-medium">{p.ticker}</span>
                  <span className="font-mono tabular-nums text-down">{formatCurrency(p.loss)}</span>
                </div>
                <svg
                  viewBox="0 0 100 8"
                  preserveAspectRatio="none"
                  className="h-2 w-full"
                  aria-hidden="true"
                >
                  <rect width="100" height="8" rx="2" fill="var(--surface-2)" />
                  <rect
                    width={maxLoss > 0 ? (Number(p.loss) / maxLoss) * 100 : 0}
                    height="8"
                    rx="2"
                    fill="var(--down)"
                    fillOpacity="0.8"
                  />
                </svg>
              </li>
            ))}
          </ol>
          <p className="mt-5 text-xs text-muted-foreground">
            Bars use the same dollar scale, starting at zero. With an equal price shock, position
            size determines the loss contribution.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
