# 0019. Durable, bounded SEC filing ingestion

- **Status:** Accepted
- **Date:** 2026-09-19

## Context

US-11 / FR-13 requires retrieving and indexing 10-K, 10-Q and 8-K filings. The user
authorized early implementation on September 19; Sprint 3 and the five-point estimate
remain unchanged. Downloading and parsing filings can outlive an HTTP request. Restarting
the web server must not silently lose work, and concurrent users must not multiply SEC
requests or duplicate public documents. The risk engine must remain independent.

## Decision

- Add a separate worker using the backend image and a durable PostgreSQL queue. A
  session advisory lock admits one worker for this deployment; interrupted jobs resume
  after restart. A lost lock connection stops processing. No Redis or broker is added.
- Authenticated API routes authorize the ticker against the caller's current holdings.
  Public issuer documents and ticker sync status are shared; account identity and portfolio
  quantities are never stored in the corpus or sent to SEC. Removing a holding revokes
  API access without deleting shared public documents.
- Resolve exact normalized ticker matches using SEC's company ticker mapping. Do not
  guess issuers or infer ETF underlying companies. Unsupported tickers are explicit.
- Initial coverage is the latest 10-K, latest 10-Q and five latest 8-K primary documents
  in the issuer's **recent submissions list**. Amendments, exhibits, fund-specific forms,
  older submissions archives and full historical coverage are excluded and labeled.
  Missing form types are reported. The bounded window is a first-release limitation,
  not a claim that all company disclosures have been ingested.
- Use fixed SEC hosts, validated accession/document names, HTTPS, no redirects,
  bounded response sizes, timeouts, an identifying User-Agent configured outside Git,
  and at most two requests/second from the sole worker. Retry transient requests with
  bounded backoff; never retry a blocked 403 in a tight loop. Refresh completed jobs no
  more often than every 15 minutes. Cache ticker mappings for 24 hours in the worker.
- Persist filing metadata, extracted text, SHA-256, extraction version, and ordered
  passages with offsets into that extracted text. Parse untrusted HTML as text only;
  scripts, styles and inline-XBRL hidden content are excluded. Each filing and its
  passages commit atomically. Failed refreshes retain previously indexed documents and
  visibly report partial or failed coverage.
- Introduce a Filings screen with real stage/count progress, source links and passage
  search. Do not render external HTML. Sources open directly on SEC.

## Consequences

The deployment gains one worker container and three tables, but keeps a single database.
Per-filing commits support resumption and deduplication; progress is completed documents,
not an invented time estimate. The worker is intentionally serial and suitable for the
capstone corpus. Multi-host deployments sharing one outbound IP need coordinated rate
limits across deployments. Plain-text extraction does not preserve financial table layout;
users can consult the original source. Live SEC access depends on a configured contact and
SEC availability. A completed job describes this bounded selection, not complete history.

## Alternatives Considered

- Synchronous HTTP ingestion: risks request timeouts and gives poor progress visibility.
- In-process background tasks: restart loses queued tasks; reload can interrupt work.
- Celery/Redis: capable but introduces another operational service for a small serial queue.
- All historical filings: unbounded time/storage and difficult first-release completeness.

Sources: [SEC APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces),
[SEC access guidance](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data).
