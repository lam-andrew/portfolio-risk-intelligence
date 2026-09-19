import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import {
  getPortfolioStress,
  getStressScenarios,
  toErrorMessage,
  type PortfolioStress,
  type StressScenario,
} from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { StatTile } from "@/components/ui/stat-tile";
import { formatCurrency } from "@/features/holdings/format";
import { StressImpactChart } from "@/features/risk/StressImpactChart";
import { ExplainLink } from "@/features/methodology/ExplainLink";

type Result =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: PortfolioStress };

/** Fetch only when requested. Changing selection/unmounting invalidates pending results. */
export function StressTestPage({ hasHoldings }: { hasHoldings: boolean }) {
  const [scenarios, setScenarios] = useState<StressScenario[]>([]);
  const [selected, setSelected] = useState("");
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [catalogAttempt, setCatalogAttempt] = useState(0);
  const [result, setResult] = useState<Result>({ kind: "idle" });
  const request = useRef(0);

  useEffect(() => {
    let active = true;
    void getStressScenarios()
      .then((items) => {
        if (!active) return;
        setScenarios(items);
        setSelected(items[0]?.id ?? "");
        setCatalogError(items.length === 0 ? "No stress scenarios are available." : null);
      })
      .catch((err: unknown) => {
        if (active) setCatalogError(toErrorMessage(err));
      });
    return () => {
      active = false;
      request.current += 1;
    };
  }, [catalogAttempt]);

  async function run() {
    const id = ++request.current;
    setResult({ kind: "loading" });
    try {
      const data = await getPortfolioStress(selected);
      if (request.current === id) setResult({ kind: "ready", data });
    } catch (err) {
      if (request.current === id) setResult({ kind: "error", message: toErrorMessage(err) });
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>What if every holding fell together?</CardTitle>
          <CardDescription>
            Apply the same assumed price decline to every position. These scenarios are
            hypothetical, with no assigned probability or time horizon.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {!hasHoldings ? (
            <p>
              Add holdings before running a stress test.{" "}
              <Link className="text-accent underline" to="/holdings">
                Open Holdings
              </Link>
            </p>
          ) : catalogError !== null ? (
            <div role="alert" className="flex flex-col items-start gap-3">
              <p>{catalogError}</p>
              <Button
                onClick={() => {
                  setCatalogError(null);
                  setCatalogAttempt((n) => n + 1);
                }}
              >
                Retry scenarios
              </Button>
            </div>
          ) : scenarios.length === 0 ? (
            <p role="status">Loading scenarios…</p>
          ) : (
            <div className="flex flex-wrap items-end gap-3">
              <div className="flex min-w-0 flex-col gap-2">
                <label htmlFor="stress-scenario" className="text-sm font-medium">
                  Scenario
                </label>
                <select
                  id="stress-scenario"
                  value={selected}
                  className="rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  onChange={(e) => {
                    request.current += 1;
                    setSelected(e.target.value);
                    setResult({ kind: "idle" });
                  }}
                >
                  {scenarios.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>
              <Button
                onClick={() => void run()}
                disabled={result.kind === "loading" || selected === ""}
              >
                {result.kind === "loading" ? "Calculating…" : "Run stress test"}
              </Button>
            </div>
          )}
          <ExplainLink anchor="stress" />
        </CardContent>
      </Card>
      <div aria-live="polite" aria-atomic="true">
        {result.kind === "loading" && <p role="status">Calculating the selected scenario…</p>}
        {result.kind === "error" && (
          <p role="alert">{result.message} Use Run stress test to retry.</p>
        )}
        {result.kind === "ready" &&
          (result.data.status === "ready" ? (
            <StressResults data={result.data} />
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>
                  {result.data.status === "empty" ? "No holdings" : "Stress estimate unavailable"}
                </CardTitle>
                <CardDescription>{result.data.message}</CardDescription>
              </CardHeader>
              {result.data.missing_tickers.length > 0 && (
                <CardContent>
                  Missing usable prices: {result.data.missing_tickers.join(", ")}
                </CardContent>
              )}
            </Card>
          ))}
      </div>
      <p className="text-xs leading-relaxed text-muted-foreground">
        This calculation holds share quantities fixed and uses adjusted closing prices, not live
        quotes. Cached prices may be stale; check the pricing date. It assumes all assets decline
        equally, including bonds and ETFs. It does not model diversification, sector sensitivity,
        fees, taxes, currency changes or trading. It is not a forecast or investment advice.
      </p>
    </div>
  );
}

function StressResults({ data }: { data: PortfolioStress }) {
  return (
    <section aria-label="Stress test results" className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h2 className="text-lg font-semibold">{data.scenario.name}</h2>
        <p className="text-sm text-muted-foreground">
          All holdings priced as of {data.as_of} · USD · latest shared date within 30 days
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <StatTile label="Baseline value" value={formatCurrency(data.baseline_value)} />
        <StatTile
          label="Estimated loss"
          value={formatCurrency(data.loss)}
          detail={`${Number(data.loss_pct).toFixed(2)}% of baseline value`}
        />
        <StatTile label="Value after scenario" value={formatCurrency(data.stressed_value)} />
      </div>
      <StressImpactChart data={data} />
      <Card>
        <CardHeader>
          <CardTitle>Loss by holding</CardTitle>
          <CardDescription>
            Under an equal shock, larger positions contribute more dollars of loss.
          </CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full text-right text-sm">
            <caption className="sr-only">Estimated impact by holding in US dollars</caption>
            <thead className="text-xs text-muted-foreground">
              <tr>
                <th scope="col" className="py-2 pr-4 text-left">
                  Holding
                </th>
                <th scope="col" className="px-3">
                  Baseline
                </th>
                <th scope="col" className="px-3">
                  Loss
                </th>
                <th scope="col" className="pl-3">
                  After scenario
                </th>
              </tr>
            </thead>
            <tbody>
              {data.positions.map((p) => (
                <tr key={p.ticker} className="border-t border-border font-mono tabular-nums">
                  <th scope="row" className="py-3 pr-4 text-left font-medium">
                    {p.ticker}
                  </th>
                  <td className="px-3">{formatCurrency(p.baseline_value)}</td>
                  <td className="px-3 text-down">{formatCurrency(p.loss)}</td>
                  <td className="pl-3">{formatCurrency(p.stressed_value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-4 text-xs text-muted-foreground">
            Amounts round to cents per holding; totals sum these rows. Percentages can differ
            slightly from the assumed shock due to rounding.
          </p>
        </CardContent>
      </Card>
    </section>
  );
}
