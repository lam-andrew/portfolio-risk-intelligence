import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import axios from "axios";
import {
  askDocumentQuestion,
  getDocumentQuestionStatus,
  getFilingDocument,
  toErrorMessage,
  type FilingAnswer,
  type FilingDocument,
  type QuestionStatus,
} from "@/api/client";
import { QuestionPrivacy } from "@/components/QuestionPrivacy";
import { Button } from "@/components/ui/button";

type Citation = FilingAnswer["claims"][number]["citations"][number];
type Exchange = { question: string; answer: FilingAnswer };
const suggestions = [
  "What are the main risks in this filing?",
  "What supplier dependencies does it disclose?",
  "What changed during the reporting period?",
];

export function FilingReaderPage() {
  const { ticker = "", accession = "" } = useParams();
  const [attempt, setAttempt] = useState(0);
  return (
    <FilingReader
      key={`${ticker}:${accession}:${attempt}`}
      ticker={ticker}
      accession={accession}
      reopen={() => setAttempt((n) => n + 1)}
    />
  );
}

/** Route/account unmount clears this session. Closing chat does not. No persistent history. */
export function FilingReader({
  ticker,
  accession,
  reopen,
}: {
  ticker: string;
  accession: string;
  reopen: () => void;
}) {
  const [document, setDocument] = useState<FilingDocument | null>(null);
  const [status, setStatus] = useState<QuestionStatus | null>(null);
  const [readError, setReadError] = useState("");
  const [chatError, setChatError] = useState("");
  const [statusError, setStatusError] = useState("");
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [busy, setBusy] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [highlight, setHighlight] = useState<Citation | null>(null);
  const [announcement, setAnnouncement] = useState("");
  const [mobile, setMobile] = useState(window.innerWidth < 900);
  const [viewportHeight, setViewportHeight] = useState<number | undefined>();
  const alive = useRef(false);
  const pending = useRef(false);
  const controller = useRef<AbortController | null>(null);
  const chat = useRef<HTMLElement>(null);
  const composer = useRef<HTMLTextAreaElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const end = useRef<HTMLDivElement>(null);
  const readerBody = useRef<HTMLDivElement>(null);
  const chatHistory = useRef<HTMLDivElement>(null);
  const passageRequest = useRef(0);
  useEffect(() => {
    alive.current = true;
    let active = true;
    const abort = new AbortController();
    controller.current = abort;
    let timer: ReturnType<typeof setTimeout>;
    void getFilingDocument(ticker, accession, {}, abort.signal)
      .then((value) => {
        if (active) {
          setDocument(value);
          setReadError("");
        }
      })
      .catch((error: unknown) => {
        if (active) setReadError(toErrorMessage(error));
      });
    async function readiness() {
      try {
        const value = await getDocumentQuestionStatus(ticker, accession, abort.signal);
        if (!active) return;
        setStatus(value);
        setStatusError("");
        if (!value.ready && value.configured) timer = setTimeout(() => void readiness(), 5000);
      } catch (error) {
        if (active) setStatusError(toErrorMessage(error));
      }
    }
    void readiness();
    return () => {
      active = false;
      alive.current = false;
      abort.abort();
      clearTimeout(timer);
    };
  }, [ticker, accession]);
  useEffect(() => {
    const resize = () => {
      setMobile(window.innerWidth < 900);
      setViewportHeight(window.visualViewport?.height);
    };
    resize();
    window.addEventListener("resize", resize);
    window.visualViewport?.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      window.visualViewport?.removeEventListener("resize", resize);
    };
  }, []);
  useEffect(() => {
    if (!open) return;
    composer.current?.focus({ preventScroll: true });
    const previousOverflow = window.document.body.style.overflow;
    if (mobile) window.document.body.style.overflow = "hidden";
    const key = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setOpen(false);
      }
      if (!mobile || event.key !== "Tab") return;
      const controls = chat.current?.querySelectorAll<HTMLElement>(
        "button:not(:disabled), textarea, a[href]",
      );
      if (!controls?.length) return;
      const first = controls[0],
        last = controls[controls.length - 1];
      if (event.shiftKey && window.document.activeElement === first) {
        event.preventDefault();
        last.focus();
      }
      if (!event.shiftKey && window.document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    const panel = chat.current;
    const opener = trigger.current;
    panel?.addEventListener("keydown", key);
    return () => {
      panel?.removeEventListener("keydown", key);
      window.document.body.style.overflow = previousOverflow;
      opener?.focus({ preventScroll: true });
    };
  }, [open, mobile]);
  useEffect(() => {
    if (open && chatHistory.current)
      chatHistory.current.scrollTop = chatHistory.current.scrollHeight;
  }, [exchanges, busy, open]);
  useEffect(() => {
    if (!highlight || (mobile && open)) return;
    const target = window.document.getElementById(`passage-${highlight.passage_id}`);
    const body = readerBody.current;
    if (target && body)
      body.scrollTop +=
        target.getBoundingClientRect().top -
        body.getBoundingClientRect().top -
        body.clientHeight / 3;
    if (mobile) trigger.current?.scrollIntoView?.({ block: "start", behavior: "auto" });
    target?.focus({ preventScroll: true });
  }, [highlight, document, mobile, open]);

  function errorMessage(error: unknown) {
    if (axios.isAxiosError(error) && [401, 404].includes(error.response?.status ?? 0)) {
      controller.current?.abort();
      setExchanges([]);
      setDraft("");
      setDocument(null);
      setReadError(
        "This filing is no longer accessible. Return to your holdings or sign in again.",
      );
    }
    if (
      axios.isAxiosError(error) &&
      error.response?.status === 409 &&
      toErrorMessage(error).includes("filing changed")
    ) {
      setExchanges([]);
      setStatus(null);
      setReadError(toErrorMessage(error));
    }
    return toErrorMessage(error);
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!document || !status?.ready || pending.current || draft.trim().length < 5) return;
    pending.current = true;
    setBusy(true);
    setChatError("");
    const question = draft.trim();
    const history = exchanges.slice(-3).map((turn) => ({
      accession,
      question: turn.question,
      answer: (
        turn.answer.claims.map((claim) => claim.text).join(" ") || turn.answer.message
      ).slice(0, 1000),
    }));
    try {
      const answer = await askDocumentQuestion(
        ticker,
        accession,
        { question, revision: document.revision, history },
        controller.current?.signal,
      );
      if (!alive.current) return;
      // Defense in depth: never display an incorrectly scoped response, even from a broken server.
      if (answer.claims.some((c) => c.citations.some((ref) => ref.accession !== accession)))
        throw new Error("Invalid filing scope");
      setExchanges((old) => [...old.slice(-19), { question, answer }]);
      setDraft("");
      setAnnouncement(
        answer.status === "answered"
          ? "Answer ready. Source citations are available."
          : answer.message,
      );
    } catch (error) {
      if (alive.current) setChatError(errorMessage(error));
    } finally {
      if (alive.current) {
        pending.current = false;
        setBusy(false);
      }
    }
  }
  async function loadPassages(citation?: Citation) {
    if (!document || loadingMore) return;
    if (citation && citation.accession !== accession) return;
    const current = ++passageRequest.current;
    if (citation && document.passages.some((p) => p.id === citation.passage_id)) {
      setHighlight(citation);
      if (mobile) setOpen(false);
      return;
    }
    setLoadingMore(true);
    try {
      const next = await getFilingDocument(
        ticker,
        accession,
        citation ? { passage_id: citation.passage_id } : { offset: document.next_offset ?? 0 },
        controller.current?.signal,
      );
      if (!alive.current || current !== passageRequest.current) return;
      if (next.revision !== document.revision) {
        setReadError("The filing changed. Reopen it to read the updated source.");
        setExchanges([]);
        setStatus(null);
        return;
      }
      setDocument(
        (old) =>
          old && {
            ...old,
            next_offset: citation ? old.next_offset : next.next_offset,
            passages: [
              ...new Map([...old.passages, ...next.passages].map((p) => [p.id, p])).values(),
            ].sort((a, b) => a.ordinal - b.ordinal),
          },
      );
      if (citation) {
        setHighlight(citation);
        if (mobile) setOpen(false);
      }
    } catch (error) {
      if (alive.current) setReadError(errorMessage(error));
    } finally {
      if (alive.current && current === passageRequest.current) setLoadingMore(false);
    }
  }

  if (!document)
    return (
      <section className="orbit-panel border border-border bg-surface p-6">
        <p role={readError ? "alert" : "status"}>{readError || "Opening filing…"}</p>
        {readError && (
          <Button className="mt-4" onClick={reopen}>
            Reopen filing
          </Button>
        )}
        <Link className="ml-4 underline" to={`/filings?ticker=${encodeURIComponent(ticker)}`}>
          Back to SEC filings
        </Link>
      </section>
    );
  const scope = `${ticker} · ${document.form} · ${document.filed_on}`;
  return (
    <div className="atlas-research">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <Link className="text-sm underline" to={`/filings?ticker=${encodeURIComponent(ticker)}`}>
          ← {ticker} filings
        </Link>
        <span className="font-mono text-xs text-muted-foreground">{document.accession}</span>
      </div>
      <div className={`atlas-reader-grid ${open ? "chat-open" : ""}`}>
        <section
          className={`atlas-reader orbit-panel ${mobile && open ? "mobile-reader-hidden" : ""}`}
          aria-label="Filing reader"
        >
          <header className="atlas-reader-header">
            <div>
              <h2 className="text-2xl">{scope}</h2>
              <p className="mt-2 text-xs text-muted-foreground">
                Indexed passages · Original layout and exhibits are not reproduced.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <a
                className="inline-flex min-h-11 items-center text-sm underline"
                href={document.source_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                Original SEC filing ↗
              </a>
              <Button ref={trigger} onClick={() => setOpen(true)} aria-expanded={open}>
                Ask about this filing
              </Button>
            </div>
          </header>
          <div
            ref={readerBody}
            className="atlas-reader-body"
            tabIndex={0}
            aria-label="Scrollable filing passages"
          >
            {readError && (
              <div role="alert" className="mb-4 rounded-xl border border-border p-4">
                {readError}{" "}
                <Button variant="outline" onClick={reopen}>
                  Reopen filing
                </Button>
              </div>
            )}
            <p className="mb-7 text-xs text-muted-foreground">
              {document.passages.length} of {document.total_passages} passages loaded. Some passages
              overlap to preserve context.
            </p>
            {document.passages.map((passage) => {
              const selected = highlight?.passage_id === passage.id ? highlight : null;
              const start = selected ? selected.start_offset - passage.start_offset : -1;
              const exact =
                selected &&
                start >= 0 &&
                passage.text.slice(start, start + selected.quote.length) === selected.quote;
              return (
                <article
                  key={passage.id}
                  id={`passage-${passage.id}`}
                  tabIndex={-1}
                  className={`atlas-passage ${selected ? "cited" : ""}`}
                >
                  <div className="mb-4 flex flex-wrap justify-between gap-2">
                    <h3 className="text-lg">{passage.section}</h3>
                    <span className="font-mono text-xs text-muted-foreground">
                      Passage {passage.ordinal + 1}
                    </span>
                  </div>
                  <p className="whitespace-pre-wrap break-words text-sm leading-7">
                    {exact ? (
                      <>
                        {passage.text.slice(0, start)}
                        <mark>{selected.quote}</mark>
                        {passage.text.slice(start + selected.quote.length)}
                      </>
                    ) : (
                      passage.text
                    )}
                  </p>
                </article>
              );
            })}
            {!document.passages.length && (
              <p>No readable passages are indexed. Open the original SEC filing.</p>
            )}
            {document.next_offset !== null && (
              <Button variant="outline" disabled={loadingMore} onClick={() => void loadPassages()}>
                {loadingMore ? "Loading passages…" : "Load more passages"}
              </Button>
            )}
          </div>
        </section>
        {open && (
          <aside
            ref={chat}
            className="atlas-chat orbit-panel"
            role={mobile ? "dialog" : "complementary"}
            aria-modal={mobile ? true : undefined}
            aria-label="Ask about this filing"
            style={mobile && viewportHeight ? { height: viewportHeight } : undefined}
          >
            <header className="atlas-chat-header">
              <div>
                <h2 className="text-xl">Ask about this filing</h2>
                <p className="mt-2 text-xs text-muted-foreground">{scope}</p>
                <span className="mt-3 inline-block rounded-md bg-surface-2 px-2 py-1 text-xs">
                  This filing only
                </span>
              </div>
              <Button
                variant="ghost"
                onClick={() => setOpen(false)}
                aria-label={mobile ? "Back to filing" : "Close chat"}
              >
                {mobile ? "Back" : "Close"}
              </Button>
            </header>
            <div ref={chatHistory} className="atlas-chat-history" aria-label="Conversation">
              <p className="mb-5 text-xs leading-relaxed text-muted-foreground">
                Answers are grounded in retrieved passages, not investment advice. Follow-ups use up
                to three prior exchanges. Only the latest 20 exchanges stay in memory; leaving this
                filing or signing out clears them.
              </p>
              {exchanges.length === 0 && (
                <div className="flex flex-col gap-3">
                  <h3 className="text-lg">Start with the disclosure.</h3>
                  <p className="text-sm text-muted-foreground">
                    Ask a specific question. Inspect the source behind each answer.
                  </p>
                  {suggestions.map((suggestion) => (
                    <button
                      key={suggestion}
                      className="atlas-suggestion"
                      onClick={() => {
                        setDraft(suggestion);
                        composer.current?.focus({ preventScroll: true });
                      }}
                    >
                      {suggestion} ↗
                    </button>
                  ))}
                </div>
              )}
              {exchanges.map((turn, index) => (
                <div className="atlas-exchange" key={index}>
                  <p className="atlas-question">
                    <span className="mb-2 block text-xs text-muted-foreground">You</span>
                    {turn.question}
                  </p>
                  <div className="atlas-answer">
                    <span className="mb-3 block font-mono text-xs text-muted-foreground">
                      ORBIT · FILING EVIDENCE
                    </span>
                    {turn.answer.status === "insufficient_evidence" ? (
                      <p>{turn.answer.message}</p>
                    ) : (
                      turn.answer.claims.map((claim, i) => (
                        <div key={i} className="mb-5">
                          <p>{claim.text}</p>
                          {claim.citations.map((citation, j) => (
                            <button
                              key={j}
                              className="atlas-citation"
                              disabled={loadingMore}
                              aria-label={`Show source passage ${citation.passage_id} for answer ${index + 1}, claim ${i + 1}`}
                              onClick={() => void loadPassages(citation)}
                            >
                              <span>
                                {citation.section} · Source {j + 1} ↗
                              </span>
                              <q className="mt-2 block text-xs text-muted-foreground">
                                {citation.quote}
                              </q>
                            </button>
                          ))}
                        </div>
                      ))
                    )}
                    <p className="mt-3 text-xs text-muted-foreground">{turn.answer.limitation}</p>
                  </div>
                </div>
              ))}
              {busy && (
                <p role="status" className="py-4 text-sm">
                  Checking passages and verifying the answer…
                </p>
              )}
              <div ref={end} />
            </div>
            <form className="atlas-composer" onSubmit={(event) => void submit(event)}>
              {statusError && (
                <p role="alert" className="mb-3 text-sm">
                  {statusError}{" "}
                  <button type="button" className="underline" onClick={reopen}>
                    Reopen filing
                  </button>
                </p>
              )}
              {!status?.ready && !statusError && (
                <p role="status" className="mb-3 text-sm">
                  {!status
                    ? "Checking question readiness…"
                    : !status.configured
                      ? "Questions are not configured. You can still read this filing."
                      : `Preparing this filing: ${status.ready_passages} of ${status.total_passages} passages ready.`}
                </p>
              )}
              {chatError && (
                <p role="alert" className="mb-3 text-sm">
                  {chatError} Your question is kept below; retry when available.
                </p>
              )}
              <label htmlFor="filing-question" className="mb-2 block text-sm">
                {exchanges.length ? "Ask a follow-up" : "Your question"}
              </label>
              <textarea
                ref={composer}
                id="filing-question"
                rows={3}
                maxLength={1000}
                minLength={5}
                required
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                readOnly={busy}
                placeholder="Ask about this disclosure…"
              />
              <div className="mt-3 flex items-center justify-between gap-3">
                <span className="text-xs text-muted-foreground">{draft.length}/1000</span>
                <Button type="submit" disabled={busy || !status?.ready || draft.trim().length < 5}>
                  {busy ? "Checking…" : "Send question"}
                </Button>
              </div>
              <QuestionPrivacy
                generator={status?.generator}
                withConversation
                className="mt-3 text-[11px] leading-relaxed text-muted-foreground"
              />
            </form>
          </aside>
        )}
      </div>
      <p className="sr-only" role="status" aria-live="polite">
        {announcement}
      </p>
    </div>
  );
}
