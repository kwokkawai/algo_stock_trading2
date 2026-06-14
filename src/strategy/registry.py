from __future__ import annotations

from typing import Type

from src.strategies.sma_crossover import SmaCrossoverStrategy
from src.strategy.base import BaseStrategy

STRATEGY_REGISTRY: dict[str, Type[BaseStrategy]] = {
    "sma_crossover": SmaCrossoverStrategy,
}


def get_strategy(name: str, params: dict) -> BaseStrategy:
    if name not in STRATEGY_REGISTRY:
        available = ", ".join(STRATEGY_REGISTRY.keys())
        raise KeyError(f"Unknown strategy '{name}'. Available: {available}")
    return STRATEGY_REGISTRY[name](params)
