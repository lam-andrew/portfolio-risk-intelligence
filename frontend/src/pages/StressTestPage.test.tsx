import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as client from "@/api/client";
import { StressTestPage } from "./StressTestPage";

const scenarios: client.StressScenario[] = [
  { id: "decline-10", name: "Broad decline · 10%", shock_pct: "-10" },
  { id: "decline-20", name: "Broad decline · 20%", shock_pct: "-20" },
];
const ready: client.PortfolioStress = {
  scenario: scenarios[1],
  status: "ready",
  as_of: "2026-09-18",
  baseline_value: "1500.00",
  loss: "300.00",
  loss_pct: "20.00",
  stressed_value: "1200.00",
  message: null,
  missing_tickers: [],
  positions: [
    { ticker: "AAPL", baseline_value: "1000.00", loss: "200.00", stressed_value: "800.00" },
    { ticker: "MSFT", baseline_value: "500.00", loss: "100.00", stressed_value: "400.00" },
  ],
};

function renderPage(hasHoldings = true) {
  return render(
    <MemoryRouter>
      <StressTestPage hasHoldings={hasHoldings} />
    </MemoryRouter>,
  );
}
async function run() {
  const button = await screen.findByRole("button", { name: "Run stress test" });
  await act(async () => {
    fireEvent.click(button);
  });
}

describe("Stress tests (US-9)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(client, "getStressScenarios").mockResolvedValue(scenarios);
    vi.spyOn(client, "getPortfolioStress").mockResolvedValue(ready);
  });

  it("runs the selected scenario and displays dated totals and contributions", async () => {
    renderPage();
    fireEvent.change(await screen.findByLabelText("Scenario"), { target: { value: "decline-20" } });
    expect(client.getPortfolioStress).not.toHaveBeenCalled();
    await run();
    const results = await screen.findByRole("region", { name: "Stress test results" });
    expect(client.getPortfolioStress).toHaveBeenCalledWith("decline-20");
    expect(
      within(results).getByRole("img", { name: /Starting value.*estimated loss.*remaining value/ }),
    ).toBeInTheDocument();
    expect(within(results).getByText("$300.00")).toBeInTheDocument();
    expect(within(results).getByText("20.00% of baseline value")).toBeInTheDocument();
    expect(within(results).getByText(/2026-09-18/)).toBeInTheDocument();
    expect(
      within(results).getByRole("row", { name: /AAPL.*1,000.00.*200.00.*800.00/ }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "How this is calculated" })).toHaveAttribute(
      "href",
      "/methodology#stress",
    );
    expect(screen.getByText(/not a forecast or investment advice/)).toBeInTheDocument();
  });

  it("shows an empty portfolio without fabricated losses", async () => {
    renderPage(false);
    expect(screen.getByRole("link", { name: "Open Holdings" })).toHaveAttribute(
      "href",
      "/holdings",
    );
    await waitFor(() => expect(client.getStressScenarios).toHaveBeenCalled());
    expect(screen.queryByRole("button", { name: "Run stress test" })).not.toBeInTheDocument();
    expect(client.getPortfolioStress).not.toHaveBeenCalled();
  });

  it("withholds totals when prices are missing", async () => {
    vi.mocked(client.getPortfolioStress).mockResolvedValue({
      ...ready,
      status: "unavailable",
      baseline_value: null,
      loss: null,
      loss_pct: null,
      stressed_value: null,
      as_of: null,
      positions: [],
      missing_tickers: ["MSFT"],
      message: "A complete estimate needs usable prices.",
    });
    renderPage();
    await run();
    expect(await screen.findByText("Stress estimate unavailable")).toBeInTheDocument();
    expect(screen.getByText(/Missing usable prices: MSFT/)).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Stress test results" })).not.toBeInTheDocument();
  });

  it("clears old results when selection changes", async () => {
    renderPage();
    await run();
    await screen.findByRole("region", { name: "Stress test results" });
    fireEvent.change(screen.getByLabelText("Scenario"), { target: { value: "decline-20" } });
    expect(screen.queryByRole("region", { name: "Stress test results" })).not.toBeInTheDocument();
  });

  it("ignores a late response after selecting and running a different scenario", async () => {
    let finish!: (data: client.PortfolioStress) => void;
    vi.mocked(client.getPortfolioStress).mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
    renderPage();
    await run();
    expect(screen.getByRole("button", { name: "Calculating…" })).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Scenario"), { target: { value: "decline-20" } });
    await run();
    await screen.findByRole("region", { name: "Stress test results" });
    await act(async () => {
      finish({ ...ready, scenario: scenarios[0], loss: "150.00" });
    });
    expect(screen.getByText("$300.00")).toBeInTheDocument();
    expect(screen.queryByText("$150.00")).not.toBeInTheDocument();
  });

  it("allows retry after an analysis error", async () => {
    vi.mocked(client.getPortfolioStress).mockRejectedValueOnce(new Error("offline"));
    renderPage();
    await run();
    expect(await screen.findByRole("alert")).toHaveTextContent(/retry/);
    await run();
    expect(await screen.findByRole("region", { name: "Stress test results" })).toBeInTheDocument();
  });

  it("allows retry after the catalogue fails", async () => {
    vi.mocked(client.getStressScenarios).mockRejectedValueOnce(new Error("offline"));
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Retry scenarios" }));
    expect(await screen.findByLabelText("Scenario")).toBeInTheDocument();
  });

  it("handles an empty catalogue", async () => {
    vi.mocked(client.getStressScenarios).mockResolvedValue([]);
    renderPage();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "No stress scenarios are available.",
    );
  });
});
