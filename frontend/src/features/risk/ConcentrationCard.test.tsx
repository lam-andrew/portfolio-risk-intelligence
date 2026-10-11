import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { ConcentrationCard } from "./ConcentrationCard";

describe("ConcentrationCard acceptance regression", () => {
  it("does not describe a 55% overweight position as evenly spread", () => {
    render(
      <MemoryRouter>
        <ConcentrationCard
          data={{
            hhi: "0.39",
            effective_holdings: "2.60",
            holdings_count: 4,
            top_1_pct: "55.00",
            top_3_pct: "90.00",
            top_5_pct: "100.00",
            overweight: [{ ticker: "BIG", weight_pct: "55.00", times_equal_weight: "2.20" }],
            overlaps: [],
            overweight_multiple: "2.0",
            overlap_threshold: "0.75",
          }}
        />
      </MemoryRouter>,
    );
    expect(screen.getByText("BIG")).toBeInTheDocument();
    expect(screen.queryByText(/spread fairly evenly/i)).not.toBeInTheDocument();
    expect(screen.getByText(/same concentration as about 2.6 equally weighted/i)).toHaveTextContent(
      "This measure does not account for correlation.",
    );
  });
});
