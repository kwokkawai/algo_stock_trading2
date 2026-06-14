"""Donchian channel breakout — Tier 1 trend following."""

from __future__ import annotations

from collections import defaultdict

from src.data.subscription import DataSubscription
from src.models.market import Bar
from src.models.signal import Signal, SignalSide
from src.strategy.base import BaseStrategy


class DonchianBreakoutStrategy(BaseStrategy):
    name = "donchian_breakout"

    def __init__(self, params: dict) -> None:
        super().__init__(params)
        interval = params.get("interval", "1d")
        self.subscription = DataSubscription(
            symbols=params.get("symbols", []),
            intervals=[interval],
        )
        self._entry = int(params.get("entry_lookback", 20))
        self._exit = int(params.get("exit_lookback", 10))
        self._qty = int(params.get("qty", 100))
        self._highs: dict[str, list[float]] = defaultdict(list)
        self._lows: dict[str, list[float]] = defaultdict(list)
        self._closes: dict[str, list[float]] = defaultdict(list)
        self._last_side: dict[str, SignalSide | None] = defaultdict(lambda: None)

    def on_bar(self, bar: Bar, interval: str) -> list[Signal]:
        expected = self.params.get("interval", "1d")
        if interval != expected:
            return []

        self._highs[bar.symbol].append(bar.high)
        self._lows[bar.symbol].append(bar.low)
        self._closes[bar.symbol].append(bar.close)

        if len(self._closes[bar.symbol]) < self._entry + 1:
            return []

        # Prior N bars (exclude current) for channel
        prior_highs = self._highs[bar.symbol][-(self._entry + 1) : -1]
        prior_lows = self._lows[bar.symbol][-(self._exit + 1) : -1]
        entry_high = max(prior_highs)
        exit_low = min(prior_lows)

        signals: list[Signal] = []

        if bar.close > entry_high and self._last_side[bar.symbol] != SignalSide.BUY:
            signals.append(
                Signal(
                    symbol=bar.symbol,
                    side=SignalSide.BUY,
                    qty=self._qty,
                    price=bar.close,
                    reason=f"Donchian breakout BUY (close>{entry_high:.2f})",
                )
            )
            self._last_side[bar.symbol] = SignalSide.BUY

        elif bar.close < exit_low and self._last_side[bar.symbol] != SignalSide.SELL:
            signals.append(
                Signal(
                    symbol=bar.symbol,
                    side=SignalSide.SELL,
                    qty=self._qty,
                    price=bar.close,
                    reason=f"Donchian breakdown SELL (close<{exit_low:.2f})",
                )
            )
            self._last_side[bar.symbol] = SignalSide.SELL

        return signals
