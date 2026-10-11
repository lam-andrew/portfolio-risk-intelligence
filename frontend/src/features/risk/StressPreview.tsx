import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getPortfolioStress, getStressScenarios, type PortfolioStress } from "@/api/client";
import { StressImpactChart } from "./StressImpactChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/** Read-only preview of the first server-owned scenario; never invent a shock or result. */
export function StressPreview() {
  const [result, setResult] = useState<PortfolioStress | null>(null);
  const [pending, setPending] = useState(true);
  useEffect(() => {
    let active = true;
    void getStressScenarios()
      .then(async (scenarios) => {
        if (!active || !scenarios.length) return;
        const next = await getPortfolioStress(scenarios[0].id);
        if (active) setResult(next);
      })
      .catch(() => {
        /* The full stress view provides retry and error details. */
      })
      .finally(() => {
        if (active) setPending(false);
      });
    return () => {
      active = false;
    };
  }, []);
  return (
    <div className="min-w-0">
      {result?.status === "ready" ? (
        <StressImpactChart data={result} compact />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>What a shock could mean</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              {pending
                ? "Loading scenario…"
                : "Scenario preview unavailable. Open stress tests to check pricing and try again."}
            </p>
          </CardContent>
        </Card>
      )}
      <Link className="mt-3 inline-block text-sm underline" to="/stress">
        Explore stress scenarios →
      </Link>
    </div>
  );
}
