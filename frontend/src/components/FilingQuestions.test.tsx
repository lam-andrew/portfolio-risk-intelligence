import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { askFilingQuestion, getQuestionStatus, type FilingAnswer } from "../api/client";
import { FilingQuestions } from "./FilingQuestions";

vi.mock("../api/client", async (original) => ({
  ...(await original<typeof import("../api/client")>()),
  askFilingQuestion: vi.fn(),
  getQuestionStatus: vi.fn(),
}));
const ready = { configured: true, total_passages: 12, ready_passages: 12, ready: true };
const answer: FilingAnswer = {
  status: "answered",
  question: "What supplier risks are disclosed?",
  message: "Answer from your filings",
  coverage: "Selected public filings.",
  limitation: "Check the original sources.",
  claims: [
    {
      text: "The company relies on one supplier.",
      citations: [
        {
          passage_id: 42,
          accession: "0000000001-26-000001",
          form: "10-K",
          filed_on: "2026-09-01",
          section: "Risk factors",
          quote: "We rely on a single supplier for certain components.",
          source_url: "https://www.sec.gov/Archives/edgar/data/1/report.htm",
          start_offset: 0,
          end_offset: 52,
        },
      ],
    },
  ],
};

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(getQuestionStatus).mockResolvedValue(ready);
  vi.mocked(askFilingQuestion).mockResolvedValue(answer);
});

async function submit() {
  await waitFor(() => expect(screen.getByLabelText("Your question")).not.toBeDisabled());
  fireEvent.change(screen.getByLabelText("Your question"), { target: { value: answer.question } });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "Ask question" }));
  });
}

describe("filing questions", () => {
  it("shows cited claims, exact quotes and original SEC links", async () => {
    render(<FilingQuestions ticker="AAPL" />);
    await submit();
    expect(await screen.findByText(answer.claims[0].text)).toBeInTheDocument();
    expect(screen.getByText(answer.claims[0].citations[0].quote)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /View original filing/ })).toHaveAttribute(
      "href",
      answer.claims[0].citations[0].source_url,
    );
    expect(askFilingQuestion).toHaveBeenCalledWith("AAPL", answer.question);
    expect(screen.getByText(/Google may use free-tier/)).toBeInTheDocument();
  });

  it("shows actual preparation progress and disables questions until ready", async () => {
    vi.mocked(getQuestionStatus).mockResolvedValue({ ...ready, ready: false, ready_passages: 3 });
    render(<FilingQuestions ticker="AAPL" />);
    const progress = await screen.findByRole("progressbar", {
      name: "Passages ready for questions",
    });
    expect(progress).toHaveAttribute("value", "3");
    expect(progress).toHaveAttribute("max", "12");
    expect(screen.getByRole("button", { name: "Ask question" })).toBeDisabled();
  });

  it("explains disabled configuration", async () => {
    vi.mocked(getQuestionStatus).mockResolvedValue({ ...ready, configured: false, ready: false });
    render(<FilingQuestions ticker="AAPL" />);
    expect(await screen.findByText(/not enabled yet/)).toBeInTheDocument();
    expect(screen.getByLabelText("Your question")).toBeDisabled();
  });

  it("shows insufficient evidence without invented claims or citations", async () => {
    vi.mocked(askFilingQuestion).mockResolvedValue({
      ...answer,
      status: "insufficient_evidence",
      claims: [],
      message: "I couldn't find enough supporting evidence.",
    });
    render(<FilingQuestions ticker="AAPL" />);
    await submit();
    expect(await screen.findByText(/couldn't find enough/)).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it("distinguishes a service error from an unsupported question and permits retry", async () => {
    vi.mocked(askFilingQuestion).mockRejectedValueOnce({
      isAxiosError: true,
      response: { data: { detail: "Free quota reached" } },
    });
    render(<FilingQuestions ticker="AAPL" />);
    await submit();
    expect(await screen.findByRole("alert")).toHaveTextContent("Free quota reached");
    expect(screen.queryByLabelText("Filing answer")).not.toBeInTheDocument();
    await submit();
    expect(await screen.findByText(answer.claims[0].text)).toBeInTheDocument();
  });

  it("cannot apply an old company's response after switching company", async () => {
    let resolve!: (value: FilingAnswer) => void;
    vi.mocked(askFilingQuestion).mockReturnValue(
      new Promise((r) => {
        resolve = r;
      }),
    );
    const view = render(<FilingQuestions key="AAPL" ticker="AAPL" />);
    await submit();
    expect(screen.getByRole("button", { name: "Checking the filings…" })).toBeDisabled();
    view.rerender(<FilingQuestions key="MSFT" ticker="MSFT" />);
    await act(async () => {
      resolve(answer);
    });
    await screen.findByText("Ask about MSFT");
    expect(screen.queryByText(answer.claims[0].text)).not.toBeInTheDocument();
    expect(screen.getByLabelText("Your question")).toHaveValue("");
  });

  it("renders provider and source markup as inert text", async () => {
    vi.mocked(askFilingQuestion).mockResolvedValue({
      ...answer,
      claims: [{ ...answer.claims[0], text: "<script>bad()</script>" }],
    });
    const view = render(<FilingQuestions ticker="AAPL" />);
    await submit();
    expect(await screen.findByText("<script>bad()</script>")).toBeInTheDocument();
    expect(view.container.querySelector("script")).toBeNull();
  });
});
