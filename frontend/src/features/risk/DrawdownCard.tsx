import { LineChart } from "@/components/charts/LineChart";
import type { PortfolioDrawdown } from "@/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ExplainLink } from "@/features/methodology/ExplainLink";

function pct(value: string | null): string {
  if (value === null) return "—";
  const n = Number(value);
  return Number.isNaN(n) ? "—" : `${n.toFixed(1)}%`;
}

function shortDate(iso: string): string {
  const d = new Date(`${iso}T00:00:00`);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "2-digit" });
}

/** Historical drawdown (US-8): how far the portfolio fell, and whether it came back. */
export function DrawdownCard({ data }: { data: PortfolioDrawdown }) {
  if (data.series.length === 0 || data.max_drawdown_pct === null) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Drawdown</CardTitle>
          <CardDescription>
            Add holdings with price history to see the portfolio&apos;s worst declines.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const current = Number(data.current_drawdown_pct ?? 0);
  const underwater = current < -0.05;

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <CardTitle>Drawdown</CardTitle>
          <ExplainLink anchor="drawdown" />
          <span className="font-mono text-xs text-faint">{data.observations} trading days</span>
        </div>
        <CardDescription>
          How far the portfolio fell from a high, and whether it recovered.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-5">
          <div className="flex flex-wrap items-end gap-x-8 gap-y-3">
            <div className="flex flex-col gap-1">
              <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
                Worst decline
              </span>
              <span className="font-mono text-3xl font-medium leading-none tabular-nums text-down">
                {pct(data.max_drawdown_pct)}
              </span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
                Currently
              </span>
              <span
                className={`font-mono text-3xl font-medium leading-none tabular-nums ${underwater ? "text-down" : "text-up"}`}
              >
                {underwater ? pct(data.current_drawdown_pct) : "At peak"}
              </span>
            </div>
          </div>

          <LineChart
            points={data.series.map((p) => ({ date: p.date, value: Number(p.drawdown_pct) }))}
            label="Portfolio drawdown"
            unit="Below running peak · %"
            color="var(--down)"
            underwater
            formatValue={(v) => `${v.toFixed(2)}%`}
          />

          {data.episodes.length > 0 && (
            <div className="flex flex-col gap-2 border-t border-border pt-4">
              <h3 className="text-sm font-medium">Largest declines</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left">
                      {["Depth", "Peak", "Trough", "Recovery"].map((h) => (
                        <th
                          key={h}
                          className="pb-1.5 font-mono text-[10px] uppercase tracking-wider text-faint last:text-right"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.episodes.map((episode) => (
                      <tr key={`${episode.peak_date}-${episode.trough_date}`}>
                        <td className="py-1.5 pr-4 font-mono tabular-nums text-down">
                          {pct(episode.depth_pct)}
                        </td>
                        <td className="py-1.5 pr-4 font-mono text-xs tabular-nums text-muted-foreground">
                          {shortDate(episode.peak_date)}
                        </td>
                        <td className="py-1.5 pr-4 font-mono text-xs tabular-nums text-muted-foreground">
                          {shortDate(episode.trough_date)} · {episode.decline_days}d
                        </td>
                        <td className="py-1.5 text-right font-mono text-xs tabular-nums">
                          {episode.recovered ? (
                            <span className="text-up">
                              {shortDate(episode.recovery_date ?? "")} · {episode.recovery_days}d
                            </span>
                          ) : (
                            <span className="text-down">not recovered</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
