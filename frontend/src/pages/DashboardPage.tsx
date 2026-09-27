import { AllocationChart } from "@/components/charts/AllocationChart";
import { LineChart } from "@/components/charts/LineChart";
import { Link } from "react-router-dom";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkline } from "@/components/ui/sparkline";
import { StatTile } from "@/components/ui/stat-tile";
import { formatCurrency } from "@/features/holdings/format";
import { HoldingsTable } from "@/features/holdings/HoldingsTable";
import { ConcentrationCard } from "@/features/risk/ConcentrationCard";
import { CorrelationCard } from "@/features/risk/CorrelationCard";
import { DrawdownCard } from "@/features/risk/DrawdownCard";
import { RiskBadge } from "@/features/risk/RiskBadge";
import { riskByTicker, type PortfolioData } from "@/hooks/usePortfolio";

function pct(value: string | null | undefined): string {
  if (value === null || value === undefined) return "—";
  const n = Number(value);
  return Number.isNaN(n) ? "—" : `${n.toFixed(1)}%`;
}

interface DashboardPageProps {
  data: PortfolioData;
  onChanged: () => void;
}

/** Risk overview (US-10): summary tiles first, then the supporting detail. */
export function DashboardPage({ data, onChanged }: DashboardPageProps) {
  const { summary, risk, correlation, history, concentration, drawdown } = data;

  if (summary.positions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No holdings yet</CardTitle>
          <CardDescription>
            Add a position or import a brokerage export to see your risk profile.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link to="/holdings" className="text-sm text-accent underline-offset-4 hover:underline">
            Go to holdings →
          </Link>
        </CardContent>
      </Card>
    );
  }

  const values = (history?.points ?? []).map((p) => Number(p.value));
  const first = values[0];
  const last = values[values.length - 1];
  const changePct = first !== undefined && first !== 0 ? ((last - first) / first) * 100 : null;
  const rising = changePct !== null && changePct >= 0;

  return (
    <div className="flex flex-col gap-4">
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatTile
          featured
          label="Portfolio value"
          value={formatCurrency(summary.total_value)}
          detail={
            changePct === null ? (
              `${summary.positions.length} positions`
            ) : (
              <span className={rising ? "text-up" : "text-down"}>
                {rising ? "+" : ""}
                {changePct.toFixed(1)}% over the window
              </span>
            )
          }
          chart={
            values.length > 1 ? (
              <Sparkline values={values} color="currentColor" label="Portfolio value over time" />
            ) : undefined
          }
        />

        <StatTile
          label="Volatility"
          value={pct(risk?.portfolio_volatility_pct)}
          badge={<RiskBadge band={risk?.portfolio_band ?? null} />}
          detail={
            risk?.diversification_benefit_pct != null
              ? `${pct(risk.undiversified_volatility_pct)} without diversification`
              : "Annualized"
          }
        />

        <StatTile
          label="Average correlation"
          value={correlation?.average_correlation ?? "—"}
          detail={
            correlation?.most_correlated[0] !== undefined
              ? `Closest pair ${correlation.most_correlated[0].a}/${correlation.most_correlated[0].b} · ${correlation.most_correlated[0].correlation}`
              : "Across all pairs"
          }
        />

        <StatTile
          label="Worst decline"
          value={pct(drawdown?.max_drawdown_pct)}
          detail={
            drawdown?.current_drawdown_pct != null && Number(drawdown.current_drawdown_pct) < -0.05
              ? `currently ${pct(drawdown.current_drawdown_pct)} below peak`
              : "recovered to peak"
          }
        />
      </section>

      {history && history.points.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Portfolio value over time</CardTitle>
            <CardDescription>
              Current share quantities replayed at historical prices. This is not your actual
              investment return.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <LineChart
              points={history.points.map((p) => ({ date: p.date, value: Number(p.value) }))}
              label="Portfolio value"
              unit="Value · USD"
              formatValue={(v) => formatCurrency(String(v))}
            />
            <p className="mt-3 text-xs text-muted-foreground">
              Source: cached market prices · {history.start} to {history.end}
            </p>
          </CardContent>
        </Card>
      )}
      <section className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Where your exposure sits</CardTitle>
            <CardDescription>
              Portfolio weight by holding. Select a holding to inspect its share.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <AllocationChart positions={summary.positions} />
          </CardContent>
        </Card>
        {correlation !== null && <CorrelationCard correlation={correlation} compact />}
      </section>
      <section className="grid gap-4">
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-baseline justify-between gap-3">
              <CardTitle>Holdings</CardTitle>
              <Link
                to="/holdings"
                className="text-xs text-accent underline-offset-4 hover:underline"
              >
                Manage
              </Link>
            </div>
            <CardDescription>Priced with end-of-day market data.</CardDescription>
          </CardHeader>
          <CardContent>
            <HoldingsTable
              positions={summary.positions}
              totalValue={summary.total_value}
              riskByTicker={riskByTicker(risk)}
              onChanged={onChanged}
            />
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        {concentration !== null && <ConcentrationCard data={concentration} />}
        {drawdown !== null && <DrawdownCard data={drawdown} />}
      </section>
    </div>
  );
}
