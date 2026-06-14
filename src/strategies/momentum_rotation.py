"""Cross-sectional momentum rotation within watchlist — Tier 1."""

from __future__ import annotations

from collections import defaultdict

from src.data.subscription import DataSubscription
from src.models.market import Bar
from src.models.signal import Signal, SignalSide
from src.strategy.base import BaseStrategy


class MomentumRotationStrategy(BaseStrategy):
    name = "momentum_rotation"

    def __init__(self, params: dict) -> None:
        super().__init__(params)
        interval = params.get("interval", "1d")
        self._symbols = list(params.get("symbols", []))
        self.subscription = DataSubscription(
            symbols=self._symbols,
            intervals=[interval],
        )
        self._lookback = int(params.get("lookback", 20))
        self._top_n = int(params.get("top_n", 1))
        self._qty = int(params.get("qty", 100))
        self._history: dict[str, list[float]] = defaultdict(list)
        self._last_side: dict[str, SignalSide | None] = defaultdict(lambda: None)

    def on_bar(self, bar: Bar, interval: str) -> list[Signal]:
        expected = self.params.get("interval", "1d")
        if interval != expected:
            return []

        self._history[bar.symbol].append(bar.close)

        # Rebalance once after the last symbol in watchlist is processed
        if not self._symbols or bar.symbol != self._symbols[-1]:
            return []

        if not self._all_ready():
            return []

        scores = self._momentum_scores()
        ranked = sorted(scores.keys(), key=lambda s: scores[s], reverse=True)
        leaders = set(ranked[: self._top_n])

        signals: list[Signal] = []
        for symbol in self._symbols:
            close = self._history[symbol][-1]
            if symbol in leaders and self._last_side[symbol] != SignalSide.BUY:
                signals.append(
                    Signal(
                        symbol=symbol,
                        side=SignalSide.BUY,
                        qty=self._qty,
                        price=close,
                        reason=f"Momentum rotation BUY (score={scores[symbol]:.2%})",
                    )
                )
                self._last_side[symbol] = SignalSide.BUY
            elif symbol not in leaders and self._last_side[symbol] == SignalSide.BUY:
                signals.append(
                    Signal(
                        symbol=symbol,
                        side=SignalSide.SELL,
                        qty=self._qty,
                        price=close,
                        reason=f"Momentum rotation SELL (score={scores[symbol]:.2%})",
                    )
                )
                self._last_side[symbol] = SignalSide.SELL

        return signals

    def _all_ready(self) -> bool:
        need = self._lookback + 1
        return all(len(self._history[s]) >= need for s in self._symbols)

    def _momentum_scores(self) -> dict[str, float]:
        scores: dict[str, float] = {}
        for symbol in self._symbols:
            hist = self._history[symbol]
            past = hist[-self._lookback - 1]
            if past == 0:
                scores[symbol] = 0.0
            else:
                scores[symbol] = hist[-1] / past - 1.0
        return scores
