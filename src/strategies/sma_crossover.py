"""SMA crossover strategy — example for daily and 1-minute bars."""

from __future__ import annotations

from collections import defaultdict

from src.data.subscription import DataSubscription
from src.models.market import Bar
from src.models.signal import Signal, SignalSide
from src.strategy.base import BaseStrategy


class SmaCrossoverStrategy(BaseStrategy):
    name = "sma_crossover"

    def __init__(self, params: dict) -> None:
        super().__init__(params)
        interval = params.get("interval", "1d")
        self.subscription = DataSubscription(
            symbols=params.get("symbols", []),
            intervals=[interval],
        )
        self._fast = int(params.get("fast_period", 10))
        self._slow = int(params.get("slow_period", 30))
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

        fast_sma = sum(history[-self._fast :]) / self._fast
        slow_sma = sum(history[-self._slow :]) / self._slow

        prev_history = history[:-1]
        if len(prev_history) < self._slow:
            return []

        prev_fast = sum(prev_history[-self._fast :]) / self._fast
        prev_slow = sum(prev_history[-self._slow :]) / self._slow

        signals: list[Signal] = []

        if prev_fast <= prev_slow and fast_sma > slow_sma:
            if self._last_side[bar.symbol] != SignalSide.BUY:
                signals.append(
                    Signal(
                        symbol=bar.symbol,
                        side=SignalSide.BUY,
                        qty=self._qty,
                        price=bar.close,
                        reason=f"SMA crossover BUY (fast={fast_sma:.2f}, slow={slow_sma:.2f})",
                    )
                )
                self._last_side[bar.symbol] = SignalSide.BUY

        elif prev_fast >= prev_slow and fast_sma < slow_sma:
            if self._last_side[bar.symbol] != SignalSide.SELL:
                signals.append(
                    Signal(
                        symbol=bar.symbol,
                        side=SignalSide.SELL,
                        qty=self._qty,
                        price=bar.close,
                        reason=f"SMA crossover SELL (fast={fast_sma:.2f}, slow={slow_sma:.2f})",
                    )
                )
                self._last_side[bar.symbol] = SignalSide.SELL

        return signals
