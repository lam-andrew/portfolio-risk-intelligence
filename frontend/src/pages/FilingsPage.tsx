import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import {
  getFilings,
  getFilingCompanies,
  addWatch,
  removeWatch,
  ingestFilings,
  searchFilings,
  toErrorMessage,
  type FilingHit,
  type FilingOverview,
  type TrackedCompanies,
  type FilingSync,
} from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const statusLabels: Record<FilingSync["status"], string> = {
  idle: "Waiting for automatic retrieval",
  queued: "Queued",
  running: "Retrieving filings",
  ready: "Indexed",
  partial: "Some downloads failed",
  failed: "Download failed",
  unsupported: "No supported filings",
};

export function FilingsPage() {
  const [tracked, setTracked] = useState<TrackedCompanies | null>(null);
  const [ticker, setTicker] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [input, setInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [watchError, setWatchError] = useState<string | null>(null);
  const [notice, setNotice] = useState("");
  const request = useRef(0);
  const mounted = useRef(true);
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
      const current = ++request.current;
      try {
        const next = await getFilingCompanies();
        if (!active || current !== request.current) return;
        setTracked(next);
        setTicker((old) =>
          next.companies.some((c) => c.ticker === old)
            ? old
            : (next.companies.find((c) => c.held)?.ticker ?? next.companies[0]?.ticker ?? ""),
        );
        setError(null);
      } catch (err) {
        if (active && current === request.current) setError(toErrorMessage(err));
      } finally {
        if (active) timer = setTimeout(() => void refresh(), 10000);
      }
    }
    void refresh();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [attempt]);

  async function updateWatch(symbol: string, add: boolean) {
    setSaving(true);
    setWatchError(null);
    setNotice("");
    // Invalidate an older list read before mutation so it cannot restore removed membership.
    request.current += 1;
    try {
      if (add) await addWatch(symbol);
      else await removeWatch(symbol);
      if (!mounted.current) return;
      request.current += 1;
      // Apply confirmed membership immediately; the next list read supplies shared status.
      setTracked((old) => {
        if (!old) return old;
        const companies = old.companies
          .map((c) => (c.ticker === symbol ? { ...c, watched: add } : c))
          .filter((c) => c.held || c.watched);
        if (add && !companies.some((c) => c.ticker === symbol))
          companies.push({
            ticker: symbol,
            held: false,
            watched: true,
            sync: {
              ticker: symbol,
              status: "idle",
              stage: "Not started",
              cik: null,
              company: null,
              completed: 0,
              total: 0,
              message: null,
              updated_at: null,
            },
          });
        return { ...old, companies };
      });
      if (add) {
        setInput("");
        setTicker(symbol);
      }
      setNotice(
        add ? `${symbol} added to your watchlist.` : `${symbol} removed from your watchlist.`,
      );
      setAttempt((n) => n + 1);
    } catch (err) {
      if (mounted.current) setWatchError(toErrorMessage(err));
    } finally {
      if (mounted.current) setSaving(false);
    }
  }
  const companies = tracked?.companies ?? [];
  // Removing the selected watch-only company must unmount its sources immediately.
  const selected = companies.some((c) => c.ticker === ticker)
    ? ticker
    : (companies[0]?.ticker ?? "");
  return (
    <div className="flex flex-col gap-6">
      {error && (
        <div role="alert">
          {error} <Button onClick={() => setAttempt((n) => n + 1)}>Retry companies</Button>
        </div>
      )}
      {!tracked && !error && <p role="status">Loading companies…</p>}
      {tracked && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Filings that follow your interests</CardTitle>
              <CardDescription>
                Orbit automatically retrieves filings for your holdings and watchlist, then checks
                for new filings daily. New companies join the background queue; larger queues can
                take longer.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-5">
              {!tracked.configured && (
                <p className="text-sm text-muted-foreground">
                  Automatic downloads are paused until SEC access is configured. Your watchlist is
                  saved and cached filings remain available.
                </p>
              )}
              <div className="flex flex-col gap-2">
                <h2 className="text-sm font-semibold">From your holdings</h2>
                <div className="flex flex-wrap gap-2">
                  {companies
                    .filter((c) => c.held)
                    .map((c) => (
                      <Button
                        key={c.ticker}
                        variant={selected === c.ticker ? "default" : "outline"}
                        size="sm"
                        aria-pressed={selected === c.ticker}
                        onClick={() => setTicker(c.ticker)}
                      >
                        {c.ticker}
                        <span className="text-xs opacity-75">{statusLabels[c.sync.status]}</span>
                      </Button>
                    ))}
                  {!companies.some((c) => c.held) && (
                    <p className="text-sm text-muted-foreground">
                      No holdings yet.{" "}
                      <Link className="text-accent underline" to="/holdings">
                        Open Holdings
                      </Link>{" "}
                      or follow a company below.
                    </p>
                  )}
                </div>
              </div>
              <div className="flex flex-col gap-3 border-t border-border pt-4">
                <div>
                  <h2 className="text-sm font-semibold">Watchlist</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Follow up to 100 companies without adding them to your portfolio. Watches do not
                    affect risk calculations.
                  </p>
                </div>
                <form
                  className="flex flex-col gap-2 sm:flex-row sm:items-end"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void updateWatch(input.trim().toUpperCase(), true);
                  }}
                >
                  <div className="flex flex-1 flex-col gap-2">
                    <label htmlFor="watch-ticker" className="text-sm">
                      Company ticker
                    </label>
                    <Input
                      id="watch-ticker"
                      placeholder="e.g. MSFT"
                      value={input}
                      onChange={(event) => setInput(event.target.value)}
                      maxLength={12}
                      required
                      autoCapitalize="characters"
                      autoComplete="off"
                    />
                  </div>
                  <Button type="submit" disabled={saving || !input.trim()}>
                    Add to watchlist
                  </Button>
                </form>
                {watchError && (
                  <p role="alert" className="text-sm">
                    {watchError}
                  </p>
                )}
                {notice && (
                  <p role="status" className="text-sm text-muted-foreground">
                    {notice}
                  </p>
                )}
                <ul className="divide-y divide-border">
                  {companies
                    .filter((c) => c.watched)
                    .map((c) => (
                      <li
                        key={c.ticker}
                        className="flex flex-wrap items-center justify-between gap-2 py-2"
                      >
                        <button
                          className="flex flex-wrap items-baseline gap-x-3 gap-y-1 text-left text-sm"
                          aria-pressed={selected === c.ticker}
                          onClick={() => setTicker(c.ticker)}
                        >
                          <span className="font-semibold text-accent">{c.ticker}</span>
                          <span className="text-muted-foreground">
                            {statusLabels[c.sync.status]}
                            {c.held ? " · Also held" : ""}
                          </span>
                        </button>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={saving}
                          aria-label={`Remove ${c.ticker} from watchlist`}
                          onClick={() => void updateWatch(c.ticker, false)}
                        >
                          Remove
                        </Button>
                      </li>
                    ))}
                </ul>
                {!companies.some((c) => c.watched) && (
                  <p className="text-sm text-muted-foreground">
                    Your watchlist is empty. Add a ticker to start following its filings.
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
          {selected && (
            <>
              <div className="flex flex-col gap-2">
                <label htmlFor="filing-company" className="text-sm font-medium">
                  Company
                </label>
                <select
                  id="filing-company"
                  value={selected}
                  onChange={(event) => setTicker(event.target.value)}
                  className="max-w-sm rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {companies.map((c) => (
                    <option key={c.ticker} value={c.ticker}>
                      {c.ticker} · {c.held ? "Holding" : "Watchlist"}
                      {c.held && c.watched ? " + Watchlist" : ""}
                    </option>
                  ))}
                </select>
              </div>
              <HoldingFilings key={selected} ticker={selected} />
            </>
          )}
        </>
      )}
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
        if (next.configured)
          timer = setTimeout(
            () => void refresh(),
            ["idle", "queued", "running"].includes(next.sync.status) ? 2000 : 10000,
          );
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
                <p className="text-sm">
                  {sync.status === "idle" && overview.configured
                    ? "Waiting for automatic retrieval. You can also start it now."
                    : sync.stage}
                </p>
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
                New filings are checked daily. Failed downloads retry hourly; unsupported companies
                are checked weekly. Manual refreshes are limited to once every 15 minutes, or 60
                seconds after a failed or partial run.
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
