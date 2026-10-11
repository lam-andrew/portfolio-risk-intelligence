import { useState, type CSSProperties } from "react";
import { Link } from "react-router-dom";

import type { PortfolioCorrelation } from "@/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ExplainLink } from "@/features/methodology/ExplainLink";

/** Diverging scale for a correlation cell.
 *
 *  Per docs/design/ui-direction.md: blue = moves opposite (diversifying), neutral grey = no
 *  relationship, red = moves together (concentration). A diverging scale is the correct form
 *  because 0 is a meaningful midpoint, not merely the low end — a sequential ramp would hide
 *  the difference between "unrelated" and "hedged". Colour is always paired with the printed
 *  number, so the value is never conveyed by hue alone. */
function cellStyle(value: number): { background: string; color: string } {
  const magnitude = Math.min(Math.abs(value), 1);
  const pole = value >= 0 ? "var(--down)" : "var(--accent)";
  return {
    background: `color-mix(in srgb, ${pole} ${magnitude * 35}%, var(--surface-2))`,
    color: "var(--foreground)",
  };
}

function fmt(value: string | null): string {
  if (value === null) return "—";
  const n = Number(value);
  return Number.isNaN(n) ? "—" : n.toFixed(2);
}

interface CorrelationCardProps {
  correlation: PortfolioCorrelation;
  /** Dashboard mode keeps every holding in a bounded, scrollable matrix. */
  compact?: boolean;
}

/** Correlation among holdings (US-6): a heatmap plus the pairs that matter. */
export function CorrelationCard({ correlation, compact = false }: CorrelationCardProps) {
  const { tickers, matrix } = correlation;
  const [selection, setPair] = useState<[number, number]>([0, 1]);
  const pair = selection.every((i) => i < correlation.tickers.length) ? selection : [0, 1];

  if (tickers.length < 2) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Correlation</CardTitle>
          <CardDescription>How your holdings move relative to each other.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="py-6 text-center text-sm text-faint">
            Add at least two holdings with price history to see how they move together.
          </p>
        </CardContent>
      </Card>
    );
  }

  const high = Number(correlation.high_threshold);
  const top = correlation.most_correlated[0];
  const bottom = correlation.least_correlated[0];

  const count = tickers.length;
  // Bound the label column to its ticker text; values stay 44–80px square touch targets.
  const labelWidth = Math.max(
    48,
    Math.min(88, Math.max(...tickers.map((ticker) => ticker.length)) * 7 + 12),
  );
  const preferredCell = Math.max(
    44,
    Math.min(80, Math.floor(((compact ? 400 : 640) - 35) / count) - 3),
  );
  const matrixStyle = {
    "--matrix-min-width": `${labelWidth + 6 + count * 47}px`,
    "--matrix-max-width": `${labelWidth + 6 + count * (preferredCell + 3)}px`,
  } as CSSProperties;

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <CardTitle>Correlation</CardTitle>
          <span className="flex items-baseline gap-3">
            {!compact && (
              <span className="font-mono text-xs text-faint">
                {correlation.observations} trading days
              </span>
            )}
            {compact ? (
              <Link
                to="/correlation"
                className="whitespace-nowrap text-xs text-accent underline-offset-4 hover:underline"
              >
                Full matrix
              </Link>
            ) : (
              <ExplainLink anchor="correlation" />
            )}
          </span>
        </div>
        <CardDescription>
          How your holdings move relative to each other. Highly correlated positions behave like one
          bet, even when they look diversified.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div
          className={compact ? "flex flex-col gap-5" : "atlas-correlation-detail"}
          style={matrixStyle}
        >
          <div className="min-w-0 space-y-4">
            <p className="text-xs text-faint">
              {count} holdings · Select a cell to inspect a pair. Scroll for larger portfolios.
            </p>
            <div
              className={`correlation-scroll ${compact ? "correlation-scroll-compact" : ""}`}
              role="region"
              aria-label="Correlation matrix, scroll to explore all holdings"
              tabIndex={0}
            >
              <table className="correlation-matrix" style={matrixStyle}>
                <caption className="sr-only">Correlation among all {count} holdings</caption>
                <colgroup>
                  <col style={{ width: labelWidth }} />
                  {tickers.map((ticker) => (
                    <col key={ticker} />
                  ))}
                </colgroup>
                <thead>
                  <tr>
                    <th />
                    {tickers.map((ticker) => (
                      <th
                        key={ticker}
                        scope="col"
                        title={ticker}
                        className="correlation-column-label"
                      >
                        {ticker}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {tickers.map((rowTicker, i) => (
                    <tr key={rowTicker}>
                      <th scope="row" className="correlation-row-label">
                        {rowTicker}
                      </th>
                      {tickers.map((colTicker, j) => {
                        const raw = matrix[i]?.[j] ?? null;
                        const value = raw === null ? null : Number(raw);
                        const style =
                          value === null
                            ? { background: "var(--surface-2)", color: "var(--faint)" }
                            : cellStyle(value);
                        return (
                          <td
                            key={colTicker}
                            title={`${rowTicker} / ${colTicker}: ${fmt(raw)}`}
                            className="correlation-cell"
                          >
                            <button
                              type="button"
                              className="correlation-cell-button"
                              style={style}
                              aria-label={`Inspect ${rowTicker} / ${colTicker}: ${fmt(raw)}`}
                              aria-pressed={pair[0] === i && pair[1] === j}
                              onClick={() => setPair([i, j])}
                            >
                              {fmt(raw)}
                            </button>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex flex-wrap items-center gap-3 text-[11px] text-faint">
              <span>−1.0</span>
              <span
                className="h-2 max-w-[200px] flex-1 rounded-full"
                style={{
                  background: `linear-gradient(90deg, ${cellStyle(-1).background}, ${cellStyle(0).background}, ${cellStyle(1).background})`,
                }}
              />
              <span>+1.0</span>
              <span className="ml-1">diversifying → moves together</span>
            </div>
          </div>

          <div role="status" className={`rounded-xl bg-surface-2 ${compact ? "p-3" : "p-5"}`}>
            <p className="font-mono text-xs text-muted-foreground">
              SELECTED PAIR · {tickers[pair[0]]} / {tickers[pair[1]]}
            </p>
            <p className={`atlas-value my-3 ${compact ? "text-2xl" : "text-4xl"}`}>
              {fmt(matrix[pair[0]]?.[pair[1]] ?? null)}
            </p>
            {!compact && (
              <p className="text-sm text-muted-foreground">
                Daily-return co-movement in the observed window. Undefined pairs are shown as a
                dash, never a measured zero.
              </p>
            )}
          </div>
          <dl className="grid gap-x-6 gap-y-1 border-t border-border pt-4 text-sm sm:grid-cols-2">
            {top !== undefined && (
              <>
                <dt className="text-muted-foreground">
                  Most correlated
                  {Number(top.correlation) >= high && (
                    <span className="ml-2 text-xs text-down">behaves like one position</span>
                  )}
                </dt>
                <dd className="font-mono tabular-nums sm:text-right">
                  {top.a} / {top.b} · {fmt(top.correlation)}
                </dd>
              </>
            )}
            {bottom !== undefined && (
              <>
                <dt className="text-muted-foreground">Least correlated</dt>
                <dd className="font-mono tabular-nums sm:text-right">
                  {bottom.a} / {bottom.b} · {fmt(bottom.correlation)}
                </dd>
              </>
            )}
            {correlation.average_correlation !== null && (
              <>
                <dt className="text-muted-foreground">Average pair</dt>
                <dd className="font-mono tabular-nums sm:text-right">
                  {fmt(correlation.average_correlation)}
                </dd>
              </>
            )}
          </dl>
        </div>
      </CardContent>
    </Card>
  );
}
