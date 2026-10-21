"""Demo configuration must expand only the explicit synthetic-data allowlist."""

import json
from pathlib import Path

import pytest

from tests.acceptance_symbols import is_acceptance_symbol


def test_default_symbols_and_unknown_rejection(tmp_path: Path) -> None:
    fixture = tmp_path / "current.json"
    fixture.write_text('{"profile": "overlap"}')
    assert is_acceptance_symbol("AAPL", fixture)
    assert is_acceptance_symbol("BND", fixture)
    assert not is_acceptance_symbol("AMD", fixture)
    assert not is_acceptance_symbol("ZZZZ", fixture)


def test_extra_symbols_are_explicit_additions_and_reload(tmp_path: Path) -> None:
    fixture = tmp_path / "current.json"
    fixture.write_text(json.dumps({"profile": "overlap", "extra_symbols": ["AMD", "BRK.B"]}))
    assert is_acceptance_symbol("AMD", fixture)
    assert is_acceptance_symbol("BRK.B", fixture)
    assert is_acceptance_symbol("AAPL", fixture)
    assert not is_acceptance_symbol("ZZZZ", fixture)
    fixture.write_text('{"profile": "overlap", "extra_symbols": []}')
    assert not is_acceptance_symbol("AMD", fixture)


@pytest.mark.parametrize("extra", [None, "AMD", {"AMD": True}, [123], ["amd"], ["BAD SYMBOL"]])
def test_invalid_configuration_is_rejected(tmp_path: Path, extra: object) -> None:
    fixture = tmp_path / "current.json"
    fixture.write_text(json.dumps({"profile": "overlap", "extra_symbols": extra}))
    with pytest.raises(ValueError, match="extra_symbols"):
        is_acceptance_symbol("AMD", fixture)
