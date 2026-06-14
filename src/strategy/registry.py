from __future__ import annotations

from typing import Type

from src.strategies.bollinger_rsi import BollingerRsiStrategy
from src.strategies.donchian_breakout import DonchianBreakoutStrategy
from src.strategies.ema_crossover import EmaCrossoverStrategy
from src.strategies.momentum_rotation import MomentumRotationStrategy
from src.strategies.sma_crossover import SmaCrossoverStrategy
from src.strategy.base import BaseStrategy

STRATEGY_REGISTRY: dict[str, Type[BaseStrategy]] = {
    "sma_crossover": SmaCrossoverStrategy,
    "ema_crossover": EmaCrossoverStrategy,
    "donchian_breakout": DonchianBreakoutStrategy,
    "bollinger_rsi": BollingerRsiStrategy,
    "momentum_rotation": MomentumRotationStrategy,
}


def get_strategy(name: str, params: dict) -> BaseStrategy:
    if name not in STRATEGY_REGISTRY:
        available = ", ".join(STRATEGY_REGISTRY.keys())
        raise KeyError(f"Unknown strategy '{name}'. Available: {available}")
    return STRATEGY_REGISTRY[name](params)
