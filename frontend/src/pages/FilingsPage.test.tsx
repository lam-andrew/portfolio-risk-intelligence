import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as api from "@/api/client";
import { FilingsPage } from "./FilingsPage";

vi.mock("@/api/client", async (original) => ({
  ...(await original<typeof import("@/api/client")>()),
  getFilingCompanies: vi.fn(),
  addWatch: vi.fn(),
  removeWatch: vi.fn(),
  getFilings: vi.fn(),
  ingestFilings: vi.fn(),
  searchFilings: vi.fn(),
}));
const source = {
  accession: "0000000001-26-000001",
  form: "10-K",
  filed_on: "2026-09-01",
  source_url: "https://www.sec.gov/Archives/edgar/data/1/report.htm",
  passage_count: 8,
  indexed_at: "2026-09-19T12:00:00Z",
};
const ready: api.FilingOverview = {
  configured: true,
  coverage: "Latest 10-K, latest 10-Q and five latest 8-K primary documents.",
  indexed_count: 1,
  filings: [source],
  sync: {
    ticker: "AAPL",
    cik: "0000000001",
    company: "Example issuer",
    status: "ready",
    stage: "Finished",
    completed: 1,
    total: 1,
    message: null,
    updated_at: "2026-09-19T12:00:00Z",
  },
};
function show() {
  render(
    <MemoryRouter>
      <FilingsPage />
    </MemoryRouter>,
  );
}
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(api.getFilingCompanies).mockResolvedValue({
    configured: true,
    companies: [
      { ticker: "AAPL", held: true, watched: false, sync: ready.sync },
      { ticker: "MSFT", held: true, watched: false, sync: { ...ready.sync, ticker: "MSFT" } },
    ],
  });
  vi.mocked(api.getFilings).mockResolvedValue(ready);
});

describe("SEC filings", () => {
  it("shows traceable source links and real completed-document progress", async () => {
    show();
    expect(await screen.findByRole("link", { name: /10-K.*View SEC source/ })).toHaveAttribute(
      "href",
      source.source_url,
    );
    expect(screen.getByRole("progressbar")).toHaveAttribute("value", "1");
    expect(screen.getByText(/Coverage excludes amendments/)).toBeInTheDocument();
  });
  it("queues ingestion and displays server progress", async () => {
    const queued = {
      ...ready.sync,
      status: "queued" as const,
      stage: "Queued",
      completed: 0,
      total: 0,
    };
    vi.mocked(api.ingestFilings).mockResolvedValue(queued);
    vi.mocked(api.getFilings)
      .mockResolvedValueOnce(ready)
      .mockResolvedValue({ ...ready, sync: queued });
    show();
    fireEvent.click(await screen.findByRole("button", { name: "Refresh filings" }));
    await waitFor(() => expect(api.ingestFilings).toHaveBeenCalledWith("AAPL"));
    expect(await screen.findByText("Queued")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ingestion in progress…" })).toBeDisabled();
  });
  it("searches source excerpts without rendering them as HTML", async () => {
    vi.mocked(api.searchFilings).mockResolvedValue([
      {
        ...source,
        passage_id: 3,
        section: "Item 1A. Risk Factors",
        text: "Supply chain <script>alert(1)</script>",
      },
    ]);
    show();
    fireEvent.change(await screen.findByLabelText("Keywords"), {
      target: { value: "supply chain" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Search passages" }));
    expect(await screen.findByText("Supply chain <script>alert(1)</script>")).toBeInTheDocument();
    expect(api.searchFilings).toHaveBeenCalledWith("AAPL", "supply chain");
  });
  it("distinguishes no keyword matches from absence of evidence", async () => {
    vi.mocked(api.searchFilings).mockResolvedValue([]);
    show();
    fireEvent.change(await screen.findByLabelText("Keywords"), { target: { value: "absent" } });
    fireEvent.click(screen.getByRole("button", { name: "Search passages" }));
    expect(
      await screen.findByText(/does not prove the filings contain no relevant evidence/),
    ).toBeInTheDocument();
  });
  it("shows configuration, partial coverage and retry failures honestly", async () => {
    vi.mocked(api.getFilings).mockResolvedValue({
      ...ready,
      configured: false,
      sync: { ...ready.sync, status: "partial", message: "One document failed." },
    });
    show();
    expect(await screen.findByText("One document failed.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Refresh filings" })).toBeDisabled();
    expect(screen.getByText(/downloads are not configured/)).toBeInTheDocument();
  });
  it("keeps indexed sources visible when refresh fails", async () => {
    vi.mocked(api.ingestFilings).mockRejectedValue(new Error("Please retry later."));
    show();
    fireEvent.click(await screen.findByRole("button", { name: "Refresh filings" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Something went wrong. Please try again.",
    );
    expect(screen.getByRole("link", { name: /10-K.*View SEC source/ })).toBeInTheDocument();
  });
  it("ignores results for a holding after selection changes", async () => {
    let resolve!: (value: api.FilingHit[]) => void;
    vi.mocked(api.searchFilings).mockReturnValue(
      new Promise((done) => {
        resolve = done;
      }),
    );
    show();
    fireEvent.change(await screen.findByLabelText("Keywords"), { target: { value: "supply" } });
    fireEvent.click(screen.getByRole("button", { name: "Search passages" }));
    fireEvent.change(screen.getByLabelText("Company"), { target: { value: "MSFT" } });
    resolve([{ ...source, passage_id: 1, section: "Old holding", text: "Stale answer" }]);
    await waitFor(() => expect(api.getFilings).toHaveBeenCalledWith("MSFT"));
    expect(screen.queryByText("Stale answer")).not.toBeInTheDocument();
  });
  it("offers holdings entry for an empty portfolio", async () => {
    vi.mocked(api.getFilingCompanies).mockResolvedValue({ configured: true, companies: [] });
    show();
    expect(await screen.findByRole("link", { name: "Open Holdings" })).toHaveAttribute(
      "href",
      "/holdings",
    );
    expect(api.getFilings).not.toHaveBeenCalled();
  });
  it("retries failed status reads", async () => {
    vi.mocked(api.getFilings)
      .mockRejectedValueOnce(new Error("Unavailable"))
      .mockResolvedValue(ready);
    show();
    fireEvent.click(await screen.findByRole("button", { name: "Refresh status" }));
    expect(await screen.findByRole("link", { name: /10-K.*View SEC source/ })).toBeInTheDocument();
  });
});

describe("automatic filing following", () => {
  it("adds a watch with no holdings and selects its automatically scheduled filings", async () => {
    const empty = { configured: true, companies: [] };
    vi.mocked(api.getFilingCompanies).mockResolvedValue(empty);
    vi.mocked(api.addWatch).mockImplementation(async () => {
      vi.mocked(api.getFilingCompanies).mockResolvedValue({
        configured: true,
        companies: [
          {
            ticker: "MSFT",
            held: false,
            watched: true,
            sync: { ...ready.sync, ticker: "MSFT", status: "queued" },
          },
        ],
      });
    });
    show();
    fireEvent.change(await screen.findByLabelText("Company ticker"), {
      target: { value: " msft " },
    });
    fireEvent.click(screen.getByRole("button", { name: "Add to watchlist" }));
    expect(await screen.findByText("MSFT added to your watchlist.")).toBeInTheDocument();
    expect(api.addWatch).toHaveBeenCalledWith("MSFT");
    await waitFor(() => expect(api.getFilings).toHaveBeenCalledWith("MSFT"));
    expect(api.ingestFilings).not.toHaveBeenCalled();
    expect(screen.getByText(/Watches do not affect risk/)).toBeInTheDocument();
  });
  it("keeps input and displays errors when adding fails", async () => {
    vi.mocked(api.addWatch).mockRejectedValue(new Error("Failed"));
    show();
    fireEvent.change(await screen.findByLabelText("Company ticker"), { target: { value: "bad" } });
    fireEvent.click(screen.getByRole("button", { name: "Add to watchlist" }));
    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByLabelText("Company ticker")).toHaveValue("bad");
    expect(screen.queryByText(/added to your watchlist/)).not.toBeInTheDocument();
  });
  it("removes selected watch-only sources immediately and ignores an older list response", async () => {
    const watched = {
      configured: true,
      companies: [{ ticker: "AAPL", held: false, watched: true, sync: ready.sync }],
    };
    vi.mocked(api.getFilingCompanies).mockResolvedValueOnce(watched);
    let resolveOld!: (value: api.TrackedCompanies) => void;
    vi.mocked(api.getFilingCompanies).mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveOld = resolve;
        }),
    );
    vi.useFakeTimers();
    try {
      await act(async () => {
        show();
      });
      expect(screen.getByLabelText("Keywords")).toBeInTheDocument();
      await act(async () => {
        await vi.advanceTimersByTimeAsync(10000);
      });
      vi.mocked(api.getFilingCompanies).mockResolvedValue({ configured: true, companies: [] });
      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: "Remove AAPL from watchlist" }));
      });
      await act(async () => {
        resolveOld(watched);
      });
      expect(screen.queryByLabelText("Keywords")).not.toBeInTheDocument();
      expect(screen.queryByLabelText("Company")).not.toBeInTheDocument();
      expect(api.removeWatch).toHaveBeenCalledWith("AAPL");
    } finally {
      vi.useRealTimers();
    }
  });
  it("keeps a held company available when removing its watch", async () => {
    vi.mocked(api.getFilingCompanies).mockResolvedValue({
      configured: true,
      companies: [{ ticker: "AAPL", held: true, watched: true, sync: ready.sync }],
    });
    vi.mocked(api.removeWatch).mockImplementation(async () => {
      vi.mocked(api.getFilingCompanies).mockResolvedValue({
        configured: true,
        companies: [{ ticker: "AAPL", held: true, watched: false, sync: ready.sync }],
      });
    });
    show();
    fireEvent.click(await screen.findByRole("button", { name: "Remove AAPL from watchlist" }));
    expect(await screen.findByText("AAPL removed from your watchlist.")).toBeInTheDocument();
    expect(screen.getByLabelText("Company")).toHaveValue("AAPL");
    expect(await screen.findByLabelText("Keywords")).toBeInTheDocument();
  });
  it("keeps membership and reports a failed removal", async () => {
    vi.mocked(api.getFilingCompanies).mockResolvedValue({
      configured: true,
      companies: [{ ticker: "AAPL", held: false, watched: true, sync: ready.sync }],
    });
    vi.mocked(api.removeWatch).mockRejectedValue(new Error("Failed"));
    show();
    fireEvent.click(await screen.findByRole("button", { name: "Remove AAPL from watchlist" }));
    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByLabelText("Company")).toHaveValue("AAPL");
  });
  it("polls idle companies until the worker discovers them without a manual click", async () => {
    vi.mocked(api.getFilings)
      .mockResolvedValueOnce({
        ...ready,
        indexed_count: 0,
        filings: [],
        sync: { ...ready.sync, status: "idle", stage: "Not started" },
      })
      .mockResolvedValue(ready);
    vi.useFakeTimers();
    try {
      await act(async () => {
        show();
      });
      expect(
        screen.getByText(/Waiting for automatic retrieval. You can also start/),
      ).toBeInTheDocument();
      await act(async () => {
        await vi.advanceTimersByTimeAsync(2000);
      });
      expect(screen.getByRole("link", { name: /10-K.*View SEC source/ })).toBeInTheDocument();
      expect(api.ingestFilings).not.toHaveBeenCalled();
    } finally {
      vi.useRealTimers();
    }
  });
});
