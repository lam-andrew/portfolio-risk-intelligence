"""Deterministic price-shock arithmetic (US-9, ADR 0018). No I/O or forecasts."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


@dataclass(frozen=True)
class StressedPosition:
    ticker: str
    baseline_value: Decimal
    loss: Decimal
    stressed_value: Decimal


@dataclass(frozen=True)
class StressResult:
    positions: list[StressedPosition]
    baseline_value: Decimal
    loss: Decimal
    stressed_value: Decimal
    loss_pct: Decimal


def apply_price_shock(values: dict[str, Decimal], shock: Decimal) -> StressResult:
    """Apply one adverse proportional price change to every position.

    Money rounds half-up to cents per position; totals sum the displayed rows so they
    reconcile. Loss is a positive dollar amount. No volatility/history estimation is
    involved, so the statistical 20-return minimum does not apply.
    """
    if not shock.is_finite() or not Decimal(-1) <= shock <= Decimal(0):
        raise ValueError("Shock must be finite and between -1 and 0.")
    if not values or any(not v.is_finite() or v <= 0 for v in values.values()):
        raise ValueError("Every position needs a finite positive value.")

    positions = []
    for ticker, value in sorted(values.items()):
        baseline = value.quantize(CENT, rounding=ROUND_HALF_UP)
        loss = (baseline * -shock).quantize(CENT, rounding=ROUND_HALF_UP)
        positions.append(StressedPosition(ticker, baseline, loss, baseline - loss))
    total = sum((p.baseline_value for p in positions), Decimal(0))
    if total <= 0:
        raise ValueError("Portfolio value rounds to zero cents.")
    loss = sum((p.loss for p in positions), Decimal(0))
    return StressResult(
        positions,
        total,
        loss,
        total - loss,
        (loss / total * 100).quantize(CENT, rounding=ROUND_HALF_UP),
    )
