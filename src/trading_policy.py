"""Trading environment policy — paper-only by default until user explicitly switches."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

PAPER_ENV = "simulate"
REAL_ENV = "real"


class PaperOnlyError(RuntimeError):
    """Raised when real trading is requested while paper_only is enabled."""


def is_paper_only(settings: dict[str, Any]) -> bool:
    """Return True when all transactions must use the simulate account."""
    return settings.get("trading", {}).get("paper_only", True)


def resolve_trading_env(
    settings: dict[str, Any],
    requested: str | None = None,
) -> str:
    """
    Resolve the effective trading environment.

    When paper_only is True (default), always returns simulate regardless of
    requested env or settings.trading.env.
    """
    trading = settings.get("trading", {})
    configured = requested or trading.get("env", PAPER_ENV)

    if is_paper_only(settings):
        if configured == REAL_ENV:
            raise PaperOnlyError(
                "Real trading is disabled (trading.paper_only: true). "
                "All orders must use the Futu paper/simulate account until you "
                "explicitly set trading.paper_only: false in config/settings.yaml."
            )
        if configured != PAPER_ENV:
            logger.warning("Unknown env %r — forcing simulate (paper_only)", configured)
        return PAPER_ENV

    if configured not in (PAPER_ENV, REAL_ENV):
        logger.warning("Unknown env %r — defaulting to simulate", configured)
        return PAPER_ENV
    return configured


def apply_paper_only_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of settings with trading.env forced to simulate when paper_only."""
    settings = dict(settings)
    trading = dict(settings.get("trading", {}))
    if is_paper_only(settings):
        if trading.get("env") == REAL_ENV:
            logger.warning("settings.trading.env was 'real' — overridden to simulate (paper_only)")
        trading["env"] = PAPER_ENV
    settings["trading"] = trading
    return settings


def assert_paper_trade_allowed(settings: dict[str, Any], operation: str = "trade") -> None:
    """Fail fast before live-only scripts run."""
    if is_paper_only(settings):
        raise PaperOnlyError(
            f"Cannot {operation}: paper_only mode is active. "
            "Use run_paper.py / run_tick.py for simulate trading only."
        )
