"""Explicit symbol allowlist for the disposable browser demo, never live recognition."""

import json
import re
from pathlib import Path

KNOWN = {"AAPL", "MSFT", "NVDA", "TSLA", "VTI", "VOO", "QQQ", "BND", "BIG", "MID", "A", "B"}


def is_acceptance_symbol(ticker: str, fixture: Path) -> bool:
    """Read opt-in extra symbols on each request so rehearsals need no code changes."""
    extra = json.loads(fixture.read_text()).get("extra_symbols", [])
    if not isinstance(extra, list) or any(
        not isinstance(symbol, str) or not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,11}", symbol)
        for symbol in extra
    ):
        raise ValueError("extra_symbols must be a list of uppercase ticker symbols")
    return ticker in KNOWN or ticker in extra
