"""EMA crossover strategy — Tier 1 trend following."""

from __future__ import annotations

from collections import defaultdict

from src.data.subscription import DataSubscription
from src.models.market import Bar
from src.models.signal import Signal, SignalSide
from src.strategies.indicators import ema_series
from src.strategy.base import BaseStrategy


class EmaCrossoverStrategy(BaseStrategy):
    name = "ema_crossover"

    def __init__(self, params: dict) -> None:
        super().__init__(params)
        interval = params.get("interval", "1d")
        self.subscription = DataSubscription(
            symbols=params.get("symbols", []),
            intervals=[interval],
        )
        self._fast = int(params.get("fast_period", 12))
        self._slow = int(params.get("slow_period", 26))
        self._qty = int(params.get("qty", 100))
        self._history: dict[str, list[float]] = defaultdict(list)
        self._last_side: dict[str, SignalSide | None] = defaultdict(lambda: None)

    def on_bar(self, bar: Bar, interval: str) -> list[Signal]:
        expected = self.params.get("interval", "1d")
        if interval != expected:
            return []

        history = self._history[bar.symbol]
        history.append(bar.close)
        if len(history) < self._slow:
            return []

        fast_series = ema_series(history, self._fast)
        slow_series = ema_series(history, self._slow)
        prev_fast = fast_series[-2]
        prev_slow = slow_series[-2]
        fast_ema = fast_series[-1]
        slow_ema = slow_series[-1]

        if None in (prev_fast, prev_slow, fast_ema, slow_ema):
            return []

        signals: list[Signal] = []

        if prev_fast <= prev_slow and fast_ema > slow_ema:
            if self._last_side[bar.symbol] != SignalSide.BUY:
                signals.append(
                    Signal(
                        symbol=bar.symbol,
                        side=SignalSide.BUY,
                        qty=self._qty,
                        price=bar.close,
                        reason=f"EMA crossover BUY (fast={fast_ema:.2f}, slow={slow_ema:.2f})",
                    )
                )
                self._last_side[bar.symbol] = SignalSide.BUY

        elif prev_fast >= prev_slow and fast_ema < slow_ema:
            if self._last_side[bar.symbol] != SignalSide.SELL:
                signals.append(
                    Signal(
                        symbol=bar.symbol,
                        side=SignalSide.SELL,
                        qty=self._qty,
                        price=bar.close,
                        reason=f"EMA crossover SELL (fast={fast_ema:.2f}, slow={slow_ema:.2f})",
                    )
                )
                self._last_side[bar.symbol] = SignalSide.SELL

        return signals
