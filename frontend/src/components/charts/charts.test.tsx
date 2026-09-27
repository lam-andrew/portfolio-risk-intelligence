import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Position } from "@/api/client";
import { AllocationChart } from "./AllocationChart";
import { LineChart } from "./LineChart";
import { ValueBars } from "./ValueBars";
const positions = (weights: (string | null)[]): Position[] =>
  weights.map((weight_pct, id) => ({
    id,
    ticker: `T${id}`,
    quantity: "1",
    latest_price: "10",
    market_value: "10",
    price_as_of: "2026-09-26",
    weight_pct,
  }));
describe("Chart data and interactions", () => {
  it("groups a long allocation without losing weight and supports selection", () => {
    render(
      <AllocationChart positions={positions(["30", "20", "15", "10", "10", "5", "5", "5"])} />,
    );
    expect(screen.getByRole("img")).toHaveAccessibleName(/Other holdings 15.0%/);
    fireEvent.click(screen.getByRole("button", { name: "Other holdings 15.0%" }));
    expect(screen.getByRole("button", { name: "Other holdings 15.0%" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });
  it("does not invent allocations for unpriced holdings", () => {
    render(<AllocationChart positions={positions([null, null])} />);
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.getByText(/once holdings are priced/)).toBeInTheDocument();
  });
  it("renders one holding as a complete ring and ignores zero weights", () => {
    const { container } = render(<AllocationChart positions={positions(["100", "0"])} />);
    expect(container.querySelector("circle")).toBeInTheDocument();
    expect(screen.getAllByRole("button")).toHaveLength(1);
    expect(container.innerHTML).not.toMatch(/NaN|Infinity/);
  });
  it("exposes exact date and value through keyboard-friendly inspection", () => {
    render(
      <LineChart
        points={[
          { date: "2026-09-01", value: 100 },
          { date: "2026-09-02", value: 80 },
        ]}
        label="Value"
        unit="USD"
        formatValue={(v) => `$${v}`}
      />,
    );
    fireEvent.change(screen.getByRole("slider"), { target: { value: "0" } });
    expect(screen.getByRole("status")).toHaveTextContent("2026-09-01 · $100");
  });
  it("handles flat and single-point history without invalid coordinates", () => {
    const { container, rerender } = render(
      <LineChart
        points={[{ date: "2026-09-01", value: 0 }]}
        label="Drawdown"
        unit="%"
        underwater
        formatValue={String}
      />,
    );
    expect(screen.queryByRole("slider")).not.toBeInTheDocument();
    rerender(
      <LineChart
        points={[
          { date: "2026-09-01", value: 0 },
          { date: "2026-09-02", value: 0 },
        ]}
        label="Drawdown"
        unit="%"
        underwater
        formatValue={String}
      />,
    );
    expect(container.innerHTML).not.toMatch(/NaN|Infinity/);
  });
  it("uses a common zero baseline and correct bar proportions", () => {
    const { container } = render(
      <ValueBars
        items={[
          { label: "AAA", value: 200 },
          { label: "BBB", value: 100 },
        ]}
        label="Loss"
        unit="USD"
        formatValue={(v) => `$${v}`}
      />,
    );
    const bars = container.querySelectorAll("rect[data-bar]");
    expect(
      Number(bars[1].getAttribute("height")) / Number(bars[0].getAttribute("height")),
    ).toBeCloseTo(0.5);
    fireEvent.click(screen.getByRole("button", { name: "BBB" }));
    expect(screen.getByText("$100")).toBeInTheDocument();
  });
  it("renders zero losses with zero-height bars", () => {
    const { container } = render(
      <ValueBars
        items={[{ label: "AAA", value: 0 }]}
        label="Loss"
        unit="USD"
        formatValue={String}
      />,
    );
    expect(container.querySelector("rect[data-bar]")).toHaveAttribute("height", "0");
    expect(container.innerHTML).not.toMatch(/NaN|Infinity/);
  });
});
