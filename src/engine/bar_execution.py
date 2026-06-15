"""Per-symbol bar execution gate — avoid duplicate orders on the same bar."""

from __future__ import annotations

from datetime import datetime


class BarExecutionGate:
    """Track last executed bar per symbol (PRD E-004)."""

    def __init__(self) -> None:
        self._last_bar_key: dict[str, str] = {}

    def should_execute(self, symbol: str, bar_timestamp: datetime) -> bool:
        key = bar_timestamp.isoformat()
        if self._last_bar_key.get(symbol) == key:
            return False
        self._last_bar_key[symbol] = key
        return True

    def reset(self) -> None:
        self._last_bar_key.clear()
