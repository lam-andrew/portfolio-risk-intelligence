"""Bounded SEC client. All network calls occur in the single ingestion worker."""

import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

import httpx


class SecError(Exception):
    """Safe, user-facing failure without leaking response bodies or configuration."""


class UnsupportedIssuer(SecError):
    pass


@dataclass(frozen=True)
class FilingRef:
    accession: str
    form: str
    filed_on: date
    source_url: str


class SecClient:
    def __init__(
        self,
        email: str,
        *,
        transport: httpx.BaseTransport | None = None,
        before_request: Callable[[], None] = lambda: None,
    ) -> None:
        if re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) is None:
            raise SecError("SEC contact is not configured.")
        self.client = httpx.Client(
            headers={"User-Agent": f"Orbit academic project {email}"},
            timeout=20,
            follow_redirects=False,
            transport=transport,
        )
        self.before_request = before_request
        self.last_request = 0.0
        self.tickers: dict[str, tuple[str, str]] = {}
        self.tickers_at = 0.0

    def close(self) -> None:
        self.client.close()

    def _get(self, url: str, limit: int = 20_000_000) -> bytes:
        parsed = httpx.URL(url)
        if parsed.scheme != "https" or parsed.host not in {"www.sec.gov", "data.sec.gov"}:
            raise SecError("Invalid SEC source.")
        for attempt in range(3):
            time.sleep(max(0, 0.5 - (time.monotonic() - self.last_request)))
            self.before_request()
            self.last_request = time.monotonic()
            try:
                with self.client.stream("GET", url) as response:
                    if response.status_code in {429, 500, 502, 503, 504}:
                        if attempt < 2:
                            # Honor bounded Retry-After; otherwise stop rather than hammer SEC.
                            retry = response.headers.get("Retry-After", "")
                            delay = float(retry) if retry.isdigit() else float(2 ** (attempt + 1))
                            if delay > 30:
                                raise SecError("SEC is busy. Please retry later.")
                            time.sleep(delay)
                            continue
                        raise SecError("SEC is busy. Please retry later.")
                    if response.status_code != 200:
                        raise SecError("SEC could not provide this document. Please retry later.")
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        body.extend(chunk)
                        if len(body) > limit:
                            raise SecError("SEC document exceeds this release's size limit.")
                    return bytes(body)
            except httpx.HTTPError as exc:
                if attempt == 2:
                    raise SecError("SEC is unreachable. Please retry later.") from exc
                time.sleep(2 ** (attempt + 1))
        raise SecError("SEC request failed.")

    def _json(self, url: str) -> dict[str, Any]:
        try:
            payload = json.loads(self._get(url))
            if not isinstance(payload, dict):
                raise ValueError
            return payload
        except (ValueError, UnicodeError) as exc:
            raise SecError("SEC returned an unreadable filing catalogue.") from exc

    def issuer(self, ticker: str) -> tuple[str, str]:
        if not self.tickers or time.monotonic() - self.tickers_at > 86400:
            payload = self._json("https://www.sec.gov/files/company_tickers.json")
            result = {}
            try:
                for entry in payload.values():
                    cik = str(int(entry["cik_str"])).zfill(10)
                    if not re.fullmatch(r"\d{10}", cik):
                        raise ValueError
                    result[str(entry["ticker"]).upper().replace("-", ".")] = (
                        cik,
                        str(entry["title"])[:300],
                    )
            except (ValueError, KeyError, TypeError) as exc:
                raise SecError("SEC returned an unreadable ticker catalogue.") from exc
            self.tickers, self.tickers_at = result, time.monotonic()
        if ticker not in self.tickers:
            raise UnsupportedIssuer("No supported corporate filer matches this ticker.")
        return self.tickers[ticker]

    def recent_filings(self, cik: str) -> list[FilingRef]:
        if not re.fullmatch(r"\d{10}", cik):
            raise SecError("Invalid issuer identifier.")
        payload = self._json(f"https://data.sec.gov/submissions/CIK{cik}.json")
        try:
            if int(payload["cik"]) != int(cik):
                raise ValueError
            recent = payload["filings"]["recent"]
            columns = [
                recent[k] for k in ("accessionNumber", "form", "filingDate", "primaryDocument")
            ]
            if not all(isinstance(c, list) for c in columns) or len({len(c) for c in columns}) != 1:
                raise ValueError
            refs = []
            for accession, form, filed, document in zip(*columns, strict=True):
                if form not in {"10-K", "10-Q", "8-K"}:
                    continue
                if not re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession):
                    raise ValueError
                if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.(?:htm|html|txt)", document):
                    raise ValueError
                refs.append(
                    FilingRef(
                        accession,
                        form,
                        date.fromisoformat(filed),
                        f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
                        f"{accession.replace('-', '')}/{document}",
                    )
                )
        except (KeyError, TypeError, ValueError) as exc:
            raise SecError("SEC returned an unsupported filing catalogue.") from exc
        limits = {"10-K": 1, "10-Q": 1, "8-K": 5}
        selected: list[FilingRef] = []
        seen = set()
        for ref in sorted(refs, key=lambda r: (r.filed_on, r.accession), reverse=True):
            if limits[ref.form] and ref.accession not in seen:
                selected.append(ref)
                seen.add(ref.accession)
                limits[ref.form] -= 1
        return selected

    def document(self, ref: FilingRef) -> str:
        body = self._get(ref.source_url)
        try:
            return body.decode("utf-8")
        except UnicodeDecodeError:
            return body.decode("windows-1252", errors="replace")
