import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import {
  getFilings,
  getHoldings,
  ingestFilings,
  searchFilings,
  toErrorMessage,
  type FilingHit,
  type FilingOverview,
  type Holding,
} from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export function FilingsPage() {
  const [holdings, setHoldings] = useState<Holding[] | null>(null);
  const [ticker, setTicker] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    void getHoldings()
      .then((items) => {
        if (active) {
          setError(null);
          setHoldings(items);
          setTicker(items[0]?.ticker ?? "");
        }
      })
      .catch((err: unknown) => {
        if (active) setError(toErrorMessage(err));
      });
    return () => {
      active = false;
    };
  }, [attempt]);
  if (error)
    return (
      <div role="alert">
        {error} <Button onClick={() => setAttempt(attempt + 1)}>Retry holdings</Button>
      </div>
    );
  if (holdings === null) return <p role="status">Loading holdings…</p>;
  if (holdings.length === 0)
    return (
      <p>
        Add a holding to browse its filings.{" "}
        <Link className="text-accent underline" to="/holdings">
          Open Holdings
        </Link>
      </p>
    );
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <label htmlFor="filing-holding" className="text-sm font-medium">
          Holding
        </label>
        <select
          id="filing-holding"
          value={ticker}
          onChange={(event) => setTicker(event.target.value)}
          className="max-w-sm rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          {holdings.map((h) => (
            <option key={h.ticker} value={h.ticker}>
              {h.ticker}
            </option>
          ))}
        </select>
      </div>
      <HoldingFilings key={ticker} ticker={ticker} />
    </div>
  );
}

function HoldingFilings({ ticker }: { ticker: string }) {
  const [overview, setOverview] = useState<FilingOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [starting, setStarting] = useState(false);
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<FilingHit[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchedQuery, setSearchedQuery] = useState("");
  const mounted = useRef(true);
  const searchRequest = useRef(0);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      searchRequest.current += 1;
    };
  }, []);
  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    async function refresh() {
      try {
        const next = await getFilings(ticker);
        if (!active) return;
        setOverview(next);
        setError(null);
        if (["queued", "running"].includes(next.sync.status))
          timer = setTimeout(() => void refresh(), 2000);
      } catch (err) {
        if (active) setError(toErrorMessage(err));
      }
    }
    void refresh();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [ticker, attempt]);

  async function start() {
    setStarting(true);
    setError(null);
    try {
      const sync = await ingestFilings(ticker);
      if (mounted.current) {
        setOverview((old) => (old ? { ...old, sync } : old));
        setAttempt((n) => n + 1);
      }
    } catch (err) {
      if (mounted.current) setError(toErrorMessage(err));
    } finally {
      if (mounted.current) setStarting(false);
    }
  }
  async function search() {
    const request = ++searchRequest.current;
    setSearching(true);
    setHits(null);
    setSearchError(null);
    setSearchedQuery(query.trim());
    try {
      const result = await searchFilings(ticker, query.trim());
      if (mounted.current && request === searchRequest.current) setHits(result);
    } catch (err) {
      if (mounted.current && request === searchRequest.current) setSearchError(toErrorMessage(err));
    } finally {
      if (mounted.current && request === searchRequest.current) setSearching(false);
    }
  }
  const sync = overview?.sync;
  const busy = starting || sync?.status === "queued" || sync?.status === "running";
  return (
    <>
      {error && (
        <div role="alert" className="text-sm">
          {error}{" "}
          <Button variant="outline" onClick={() => setAttempt((n) => n + 1)}>
            Refresh status
          </Button>
        </div>
      )}
      {!overview && !error && <p role="status">Loading filings…</p>}
      {overview && sync && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>{sync.company ?? ticker} · SEC filings</CardTitle>
              <CardDescription>{overview.coverage}</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              {!overview.configured && (
                <p className="text-sm text-muted-foreground">
                  SEC downloads are not configured yet. Previously indexed filings remain
                  searchable.
                </p>
              )}
              <div className="flex flex-wrap items-center gap-3">
                <Button onClick={() => void start()} disabled={busy || !overview.configured}>
                  {busy
                    ? "Ingestion in progress…"
                    : overview.indexed_count
                      ? "Refresh filings"
                      : "Retrieve filings"}
                </Button>
                <span className="text-sm text-muted-foreground">
                  {overview.indexed_count} indexed filings
                </span>
              </div>
              <div role="status" aria-live="polite" className="flex flex-col gap-2">
                <p className="text-sm">{sync.stage}</p>
                {sync.total > 0 && (
                  <>
                    <progress
                      className="h-2 w-full accent-current text-accent"
                      aria-label="Filings indexed"
                      max={sync.total}
                      value={sync.completed}
                    />
                    <span className="text-xs text-muted-foreground">
                      {sync.completed} of {sync.total} selected documents indexed
                    </span>
                  </>
                )}
                {sync.message && <p className="text-sm text-muted-foreground">{sync.message}</p>}
                {sync.updated_at && (
                  <p className="text-xs text-muted-foreground">
                    Last status update: {new Date(sync.updated_at).toLocaleString()}
                  </p>
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                Coverage excludes amendments, exhibits, fund-specific forms and older filing
                archives. Refresh checks for new filings; previously indexed documents are retained.
                Completed refreshes are limited to once every 15 minutes.
              </p>
            </CardContent>
          </Card>
          {overview.filings.length > 0 && (
            <>
              <section aria-label="Indexed sources" className="flex flex-col gap-3">
                <h2 className="text-lg font-semibold">Indexed sources</h2>
                {overview.indexed_count > 50 && (
                  <p className="text-sm text-muted-foreground">
                    Showing the 50 most recent indexed filings. Search includes all retained
                    filings.
                  </p>
                )}
                <ul className="divide-y divide-border">
                  {overview.filings.map((f) => (
                    <li
                      key={f.accession}
                      className="flex flex-wrap items-baseline justify-between gap-2 py-3"
                    >
                      <a
                        href={f.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-medium text-accent underline"
                      >
                        {f.form} · {f.filed_on} — View SEC source
                      </a>
                      <span className="break-all text-xs text-muted-foreground">
                        {f.accession} · {f.passage_count} passages
                      </span>
                    </li>
                  ))}
                </ul>
              </section>
              <Card>
                <CardHeader>
                  <CardTitle>Search filing passages</CardTitle>
                  <CardDescription>
                    Keyword search across indexed text. These are source excerpts, not generated
                    answers.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form
                    className="flex flex-col gap-3 sm:flex-row"
                    onSubmit={(event) => {
                      event.preventDefault();
                      void search();
                    }}
                  >
                    <div className="flex flex-1 flex-col gap-2">
                      <label className="text-sm" htmlFor="filing-query">
                        Keywords
                      </label>
                      <Input
                        id="filing-query"
                        value={query}
                        onChange={(event) => setQuery(event.target.value)}
                        minLength={2}
                        maxLength={200}
                        required
                        placeholder="e.g. supply chain"
                      />
                    </div>
                    <Button
                      className="self-end"
                      type="submit"
                      disabled={searching || query.trim().length < 2}
                    >
                      {searching ? "Searching…" : "Search passages"}
                    </Button>
                  </form>
                  {searchError && (
                    <p role="alert" className="mt-4 text-sm">
                      {searchError}
                    </p>
                  )}
                  {hits && (
                    <div className="mt-5 flex flex-col gap-4" aria-live="polite">
                      <p className="text-sm text-muted-foreground">
                        {hits.length
                          ? `Top ${hits.length} matches for “${searchedQuery}”`
                          : `No matching passages for “${searchedQuery}”. Try different keywords; this does not prove the filings contain no relevant evidence.`}
                      </p>
                      {hits.map((hit) => (
                        <article key={hit.passage_id} className="border-t border-border pt-4">
                          <h3 className="text-sm font-medium">
                            {hit.form} · {hit.filed_on} · {hit.section}
                          </h3>
                          <p className="my-3 whitespace-pre-wrap break-words text-sm leading-relaxed text-muted-foreground">
                            {hit.text}
                          </p>
                          <a
                            className="text-xs text-accent underline"
                            href={hit.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            View original filing · {hit.accession}
                          </a>
                        </article>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </>
      )}
    </>
  );
}
