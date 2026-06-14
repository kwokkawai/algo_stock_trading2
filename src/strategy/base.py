from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from src.data.subscription import DataSubscription
from src.models.market import Bar, Tick
from src.models.order import Position
from src.models.signal import Signal


@dataclass
class StrategyContext:
    params: dict[str, Any]
    positions: list[Position] = field(default_factory=list)
    market: str = "HK"

    def get_position_qty(self, symbol: str) -> int:
        for pos in self.positions:
            if pos.symbol == symbol:
                return pos.qty
        return 0


class BaseStrategy(ABC):
    name: str = "base"

    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params
        self.subscription = DataSubscription(
            symbols=params.get("symbols", []),
            intervals=[params.get("interval", "1d")],
            tick=params.get("tick", False),
        )

    def on_start(self, ctx: StrategyContext) -> None:
        pass

    @abstractmethod
    def on_bar(self, bar: Bar, interval: str) -> list[Signal]:
        pass

    def on_tick(self, tick: Tick) -> list[Signal]:
        return []

    def on_stop(self, ctx: StrategyContext) -> None:
        pass
