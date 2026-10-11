import { useEffect, useRef, useState } from "react";
import {
  askFilingQuestion,
  getQuestionStatus,
  toErrorMessage,
  type FilingAnswer,
  type QuestionStatus,
} from "../api/client";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";

/** Parent keys by ticker: changing company destroys the previous question and response. */
export function FilingQuestions({ ticker }: { ticker: string }) {
  const [status, setStatus] = useState<QuestionStatus | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<FilingAnswer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const mounted = useRef(true);
  const request = useRef(0);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      request.current += 1;
    };
  }, []);

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    async function refresh() {
      try {
        const next = await getQuestionStatus(ticker);
        if (!active) return;
        setStatus(next);
        setStatusError(null);
        if (next.configured) timer = setTimeout(() => void refresh(), 10000);
      } catch (err) {
        if (active) setStatusError(toErrorMessage(err));
      }
    }
    void refresh();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [ticker, attempt]);

  async function ask() {
    const id = ++request.current;
    setBusy(true);
    setError(null);
    setAnswer(null);
    try {
      const result = await askFilingQuestion(ticker, question.trim());
      if (mounted.current && request.current === id) setAnswer(result);
    } catch (err) {
      if (mounted.current && request.current === id) setError(toErrorMessage(err));
    } finally {
      if (mounted.current && request.current === id) {
        setBusy(false);
        setAttempt((n) => n + 1);
      }
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ask about {ticker}</CardTitle>
        <CardDescription>
          Explore the disclosures with answers you can trace to the source.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {!status && !statusError && <p role="status">Checking availability…</p>}
        {statusError && (
          <p role="alert" className="text-sm">
            {statusError}{" "}
            <Button variant="outline" onClick={() => setAttempt((n) => n + 1)}>
              Check again
            </Button>
          </p>
        )}
        {status && !status.configured && (
          <p className="text-sm text-muted-foreground">
            Filing questions are not enabled yet. You can still read sources and search their text
            below.
          </p>
        )}
        {status?.configured && !status.ready && (
          <div role="status" className="flex flex-col gap-2 text-sm text-muted-foreground">
            {status.total_passages > 0 ? (
              <>
                <p>
                  Preparing filings for questions · {status.ready_passages} of{" "}
                  {status.total_passages} passages ready
                </p>
                <progress
                  aria-label="Passages ready for questions"
                  className="h-2 w-full accent-current text-accent"
                  value={status.ready_passages}
                  max={status.total_passages}
                />
                <p>
                  Preparation runs in the background and may pause when the free service reaches its
                  quota.
                </p>
              </>
            ) : (
              <p>
                Questions become available after this company’s filings have been retrieved and
                prepared.
              </p>
            )}
          </div>
        )}
        <form
          className="flex flex-col gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            void ask();
          }}
        >
          <label htmlFor="filing-question" className="text-sm font-medium">
            Your question
          </label>
          <textarea
            id="filing-question"
            className="min-h-24 w-full rounded-xl border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            minLength={5}
            maxLength={1000}
            required
            disabled={!status?.ready || busy}
            placeholder="What supply chain risks does the company disclose?"
            aria-describedby="question-privacy"
          />
          <p id="question-privacy" className="text-xs text-muted-foreground">
            Your question and relevant public filing excerpts are sent to Google’s Gemini service.
            Google may use free-tier submissions to improve its products. Keep personal or
            confidential information out of your question.
          </p>
          <Button
            className="self-start"
            type="submit"
            disabled={!status?.ready || busy || question.trim().length < 5}
          >
            {busy ? "Checking the filings…" : "Ask question"}
          </Button>
        </form>
        {busy && (
          <p role="status" className="text-sm text-muted-foreground">
            Finding relevant passages and checking the answer against its evidence…
          </p>
        )}
        {error && (
          <p role="alert" className="text-sm">
            {error}
          </p>
        )}
        {answer && (
          <section
            aria-label="Filing answer"
            aria-live="polite"
            className="flex flex-col gap-4 border-t border-border pt-4"
          >
            <h3 className="font-medium">{answer.question}</h3>
            <p className="text-sm text-muted-foreground">{answer.message}</p>
            {answer.claims.map((claim, index) => (
              <article key={index} className="flex flex-col gap-3">
                <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">
                  {claim.text}
                </p>
                {claim.citations.map((citation, i) => (
                  <details
                    key={`${citation.passage_id}-${i}`}
                    className="rounded-xl border border-border p-3"
                    open
                  >
                    <summary className="cursor-pointer text-xs font-medium">
                      {citation.form} · {citation.filed_on} · {citation.section}
                    </summary>
                    <blockquote className="my-3 whitespace-pre-wrap break-words border-l-2 border-accent pl-3 text-sm text-muted-foreground">
                      {citation.quote}
                    </blockquote>
                    <a
                      className="text-xs text-accent underline"
                      href={citation.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      View original filing · {citation.accession}
                    </a>
                  </details>
                ))}
              </article>
            ))}
            <p className="text-xs text-muted-foreground">
              {answer.coverage} {answer.limitation}
            </p>
          </section>
        )}
      </CardContent>
    </Card>
  );
}
