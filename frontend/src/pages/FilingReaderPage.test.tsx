import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { StrictMode } from "react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import * as api from "@/api/client";
import { FilingReader } from "./FilingReaderPage";

const accession = "0000000001-26-000001";
const quote = "We rely on one supplier for certain components.";
const document: api.FilingDocument = {
  ticker: "AAPL",
  accession,
  form: "10-K",
  filed_on: "2026-09-01",
  source_url: "https://www.sec.gov/Archives/edgar/data/1/a.htm",
  revision: "a".repeat(64),
  content_kind: "indexed_passages",
  total_passages: 1,
  offset: 0,
  next_offset: null,
  passages: [
    {
      id: 12,
      ordinal: 0,
      section: "Item 1A. Risk factors",
      text: quote,
      start_offset: 0,
      end_offset: quote.length,
    },
  ],
};
const answer: api.FilingAnswer = {
  status: "answered",
  question: "What supplier risks?",
  message: "Answer",
  coverage: "This filing",
  limitation: "Check the original source.",
  claims: [
    {
      text: "The company depends on one supplier.",
      citations: [
        {
          passage_id: 12,
          accession,
          form: "10-K",
          filed_on: "2026-09-01",
          section: "Item 1A. Risk factors",
          quote,
          source_url: document.source_url,
          start_offset: 0,
          end_offset: quote.length,
        },
      ],
    },
  ],
};
const reopen = vi.fn();
function view(id = accession) {
  return (
    <MemoryRouter>
      <FilingReader key={id} ticker="AAPL" accession={id} reopen={reopen} />
    </MemoryRouter>
  );
}
async function open() {
  fireEvent.click(await screen.findByRole("button", { name: "Ask about this filing" }));
}
async function ask(text = "What supplier risks?") {
  fireEvent.change(screen.getByRole("textbox"), { target: { value: text } });
  fireEvent.submit(screen.getByRole("textbox").closest("form")!);
}
beforeEach(() => {
  vi.restoreAllMocks();
  reopen.mockClear();
  window.innerWidth = 1200;
  vi.spyOn(api, "getFilingDocument").mockResolvedValue(document);
  vi.spyOn(api, "getDocumentQuestionStatus").mockResolvedValue({
    configured: true,
    total_passages: 1,
    ready_passages: 1,
    ready: true,
  });
  vi.spyOn(api, "askDocumentQuestion").mockResolvedValue(answer);
});
describe("Atlas filing research", () => {
  it("ignores an aborted initial request during Strict Mode effect replay", async () => {
    vi.mocked(api.getFilingDocument).mockImplementationOnce(
      (_t, _a, _p, signal) =>
        new Promise((_resolve, reject) =>
          signal?.addEventListener("abort", () => reject(new Error("aborted"))),
        ),
    );
    render(<StrictMode>{view()}</StrictMode>);
    await screen.findByText(quote);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
  it("opens the safe reader without starting a conversation or calling a model", async () => {
    render(view());
    expect(await screen.findByText(quote)).toBeInTheDocument();
    expect(screen.getByText(/Indexed passages/)).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(api.askDocumentQuestion).not.toHaveBeenCalled();
    await open();
    fireEvent.click(screen.getByRole("button", { name: /What supplier dependencies/ }));
    expect(screen.getByRole("textbox")).toHaveValue("What supplier dependencies does it disclose?");
    expect(api.askDocumentQuestion).not.toHaveBeenCalled();
  });
  it("sends the filing revision and bounded prior exchange on a real follow-up", async () => {
    render(view());
    await open();
    await ask();
    await screen.findByText("The company depends on one supplier.");
    await ask("Does it name those suppliers?");
    await waitFor(() => expect(api.askDocumentQuestion).toHaveBeenCalledTimes(2));
    expect(vi.mocked(api.askDocumentQuestion).mock.calls[1][2]).toEqual({
      question: "Does it name those suppliers?",
      revision: document.revision,
      history: [
        {
          accession,
          question: "What supplier risks?",
          answer: "The company depends on one supplier.",
        },
      ],
    });
  });
  it("retains a draft and answers across close/reopen and restores keyboard focus", async () => {
    render(view());
    await open();
    await ask();
    await screen.findByText("The company depends on one supplier.");
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "Another question" } });
    fireEvent.keyDown(screen.getByRole("textbox"), { key: "Escape" });
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ask about this filing" })).toHaveFocus();
    await open();
    expect(screen.getByRole("textbox")).toHaveValue("Another question");
    expect(screen.getByText("The company depends on one supplier.")).toBeInTheDocument();
  });
  it("navigates a citation to the exact highlighted source passage", async () => {
    render(view());
    await open();
    await ask();
    fireEvent.click(await screen.findByRole("button", { name: /Show source passage 12/ }));
    const mark = window.document.querySelector("mark");
    expect(mark).toHaveTextContent(quote);
    expect(window.document.getElementById("passage-12")).toHaveFocus();
  });
  it("fetches the correct bounded page for a citation beyond loaded passages", async () => {
    vi.mocked(api.getFilingDocument).mockResolvedValueOnce({
      ...document,
      passages: [],
      next_offset: 0,
    });
    render(view());
    await open();
    await ask();
    fireEvent.click(await screen.findByRole("button", { name: /Show source passage 12/ }));
    await waitFor(() => expect(window.document.querySelector("mark")).toHaveTextContent(quote));
    expect(api.getFilingDocument).toHaveBeenLastCalledWith(
      "AAPL",
      accession,
      { passage_id: 12 },
      expect.any(AbortSignal),
    );
  });
  it("uses a full-screen mobile dialog and returns to the reader on citation", async () => {
    window.innerWidth = 390;
    render(view());
    await open();
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-modal", "true");
    await ask();
    fireEvent.click(await screen.findByRole("button", { name: /Show source passage 12/ }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(window.document.querySelector("mark")).toHaveTextContent(quote);
  });
  it("guards duplicate submission and discards late answers on filing change", async () => {
    let resolve!: (a: api.FilingAnswer) => void;
    vi.mocked(api.askDocumentQuestion).mockImplementation(
      () =>
        new Promise((r) => {
          resolve = r;
        }),
    );
    const { rerender } = render(view());
    await open();
    await ask();
    await ask();
    expect(api.askDocumentQuestion).toHaveBeenCalledTimes(1);
    const signal = vi.mocked(api.askDocumentQuestion).mock.calls[0][3];
    rerender(view("0000000001-26-000002"));
    expect(signal?.aborted).toBe(true);
    await act(async () => {
      resolve(answer);
    });
    await open();
    expect(screen.queryByText("The company depends on one supplier.")).not.toBeInTheDocument();
    expect(screen.getByRole("textbox")).toHaveValue("");
  });
  it("keeps unsent text on a retryable service error", async () => {
    vi.mocked(api.askDocumentQuestion).mockRejectedValueOnce(new Error("service failed"));
    render(view());
    await open();
    await ask();
    expect(await screen.findByRole("alert")).toHaveTextContent("Your question is kept");
    expect(screen.getByRole("textbox")).toHaveValue("What supplier risks?");
    fireEvent.click(screen.getByRole("button", { name: "Send question" }));
    await screen.findByText("The company depends on one supplier.");
  });
  it("shows abstention without inventing citations", async () => {
    vi.mocked(api.askDocumentQuestion).mockResolvedValue({
      ...answer,
      status: "insufficient_evidence",
      claims: [],
      message: "No supporting evidence.",
    });
    render(view());
    await open();
    await ask();
    await screen.findAllByText("No supporting evidence.");
    expect(screen.queryByRole("button", { name: /Show source passage/ })).not.toBeInTheDocument();
  });
  it.each([false, true])(
    "keeps reading available while configured=%s and questions unavailable",
    async (configured) => {
      vi.mocked(api.getDocumentQuestionStatus).mockResolvedValue({
        configured,
        total_passages: 10,
        ready_passages: 2,
        ready: false,
      });
      render(view());
      await open();
      expect(screen.getByText(quote)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Send question" })).toBeDisabled();
      expect(
        screen.getByText(
          configured ? /Preparing this filing: 2 of 10/ : /Questions are not configured/,
        ),
      ).toBeInTheDocument();
    },
  );
  it("refuses a wrongly scoped answer from a broken server", async () => {
    vi.mocked(api.askDocumentQuestion).mockResolvedValue({
      ...answer,
      claims: [
        {
          ...answer.claims[0],
          citations: [{ ...answer.claims[0].citations[0], accession: "other" }],
        },
      ],
    });
    render(view());
    await open();
    await ask();
    await screen.findByRole("alert");
    expect(screen.queryByText("The company depends on one supplier.")).not.toBeInTheDocument();
  });
  it("aborts account-bound requests on unmount", async () => {
    const { unmount } = render(view());
    await open();
    const signal = vi.mocked(api.getFilingDocument).mock.calls[0][3];
    unmount();
    expect(signal?.aborted).toBe(true);
  });
});
