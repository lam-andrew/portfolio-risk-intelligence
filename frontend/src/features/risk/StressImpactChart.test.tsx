import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { PortfolioStress } from "@/api/client";
import { StressImpactChart } from "./StressImpactChart";

const data: PortfolioStress = {
  status: "ready",
  scenario: { id: "decline-20", name: "Broad decline · 20%", shock_pct: "-20" },
  baseline_value: "1500.00",
  loss: "300.00",
  stressed_value: "1200.00",
  loss_pct: "20.00",
  as_of: "2026-09-18",
  message: null,
  missing_tickers: [],
  positions: [
    { ticker: "MSFT", baseline_value: "500.00", loss: "100.00", stressed_value: "400.00" },
    { ticker: "AAPL", baseline_value: "1000.00", loss: "200.00", stressed_value: "800.00" },
  ],
};

describe("Stress impact charts", () => {
  it("shows a zero-based bridge with correctly proportional loss and remaining bars", () => {
    render(<StressImpactChart data={data} />);
    expect(screen.getByRole("img")).toHaveAccessibleName(
      /Starting value \$1,500.00, estimated loss \$300.00, remaining value \$1,200.00/,
    );
    const baseline = Number(
      screen
        .getByText("Baseline value", { selector: "title" })
        .parentElement?.getAttribute("height"),
    );
    const loss = Number(
      screen
        .getByText("Estimated loss step", { selector: "title" })
        .parentElement?.getAttribute("height"),
    );
    const remaining = Number(
      screen
        .getByText("Value after scenario", { selector: "title" })
        .parentElement?.getAttribute("height"),
    );
    expect(loss / baseline).toBeCloseTo(0.2);
    expect(remaining / baseline).toBeCloseTo(0.8);
    expect(screen.getByText(/not movement over time/)).toBeInTheDocument();
  });

  it("ranks contributions without mutating the API data", () => {
    render(<StressImpactChart data={data} />);
    const rows = within(
      screen.getByRole("list", { name: "Largest loss contributions" }),
    ).getAllByRole("listitem");
    expect(rows[0]).toHaveTextContent("AAPL");
    expect(rows[1]).toHaveTextContent("MSFT");
    const first = Number(rows[0].querySelector("svg rect:last-child")?.getAttribute("width"));
    const second = Number(rows[1].querySelector("svg rect:last-child")?.getAttribute("width"));
    expect(second / first).toBeCloseTo(0.5);
    expect(data.positions[0].ticker).toBe("MSFT");
  });

  it("labels the five-holding limit when there are more positions", () => {
    const positions = Array.from({ length: 6 }, (_, i) => ({
      ticker: `TEST${i}`,
      baseline_value: "100",
      loss: String(i + 1),
      stressed_value: "99",
    }));
    render(<StressImpactChart data={{ ...data, positions }} />);
    expect(screen.getByText(/five largest dollar losses/)).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(5);
    expect(screen.getAllByRole("listitem")[0]).toHaveTextContent("TEST5");
  });

  it("handles zero-cent losses without invalid bar dimensions", () => {
    const zero = {
      ...data,
      loss: "0.00",
      stressed_value: data.baseline_value,
      positions: data.positions.map((p) => ({
        ...p,
        loss: "0.00",
        stressed_value: p.baseline_value,
      })),
    };
    const { container } = render(<StressImpactChart data={zero} />);
    expect(
      screen.getByText("Estimated loss step", { selector: "title" }).parentElement,
    ).toHaveAttribute("height", "0");
    expect(container.innerHTML).not.toMatch(/NaN|Infinity/);
  });

  it("does not render an unavailable portfolio as a zero loss", () => {
    render(
      <StressImpactChart
        data={{ ...data, status: "unavailable", baseline_value: null, loss: null }}
      />,
    );
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });
});
