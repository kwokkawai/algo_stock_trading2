"""Bollinger Bands + RSI mean reversion — Tier 1."""

from __future__ import annotations

from collections import defaultdict

from src.data.subscription import DataSubscription
from src.models.market import Bar
from src.models.signal import Signal, SignalSide
from src.strategies.indicators import bollinger_bands, rsi
from src.strategy.base import BaseStrategy


class BollingerRsiStrategy(BaseStrategy):
    name = "bollinger_rsi"

    def __init__(self, params: dict) -> None:
        super().__init__(params)
        interval = params.get("interval", "1d")
        self.subscription = DataSubscription(
            symbols=params.get("symbols", []),
            intervals=[interval],
        )
        self._bb_period = int(params.get("bb_period", 20))
        self._bb_std = float(params.get("bb_std", 2.0))
        self._rsi_period = int(params.get("rsi_period", 14))
        self._rsi_buy = float(params.get("rsi_buy", 30))
        self._rsi_sell = float(params.get("rsi_sell", 70))
        self._qty = int(params.get("qty", 100))
        self._history: dict[str, list[float]] = defaultdict(list)
        self._last_side: dict[str, SignalSide | None] = defaultdict(lambda: None)

    def on_bar(self, bar: Bar, interval: str) -> list[Signal]:
        expected = self.params.get("interval", "1d")
        if interval != expected:
            return []

        history = self._history[bar.symbol]
        history.append(bar.close)

        min_len = max(self._bb_period, self._rsi_period + 1)
        if len(history) < min_len:
            return []

        bands = bollinger_bands(history, self._bb_period, self._bb_std)
        rsi_val = rsi(history, self._rsi_period)
        if bands is None or rsi_val is None:
            return []

        lower, _middle, upper = bands
        signals: list[Signal] = []

        if bar.close <= lower and rsi_val < self._rsi_buy:
            if self._last_side[bar.symbol] != SignalSide.BUY:
                signals.append(
                    Signal(
                        symbol=bar.symbol,
                        side=SignalSide.BUY,
                        qty=self._qty,
                        price=bar.close,
                        reason=f"Bollinger+RSI BUY (rsi={rsi_val:.1f}, lower={lower:.2f})",
                    )
                )
                self._last_side[bar.symbol] = SignalSide.BUY

        elif bar.close >= upper and rsi_val > self._rsi_sell:
            if self._last_side[bar.symbol] != SignalSide.SELL:
                signals.append(
                    Signal(
                        symbol=bar.symbol,
                        side=SignalSide.SELL,
                        qty=self._qty,
                        price=bar.close,
                        reason=f"Bollinger+RSI SELL (rsi={rsi_val:.1f}, upper={upper:.2f})",
                    )
                )
                self._last_side[bar.symbol] = SignalSide.SELL

        return signals
