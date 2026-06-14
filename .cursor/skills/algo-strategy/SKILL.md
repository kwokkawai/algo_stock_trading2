---
name: algo-strategy
description: >-
  Implements and modifies pluggable trading strategies for myAlgo2. Strategies
  extend BaseStrategy, declare DataSubscription, and output Signal objects only.
  Use when the user asks to create, change, or review algorithms, indicators,
  SMA, momentum, tick strategies, or LLM-recommended trading logic. Never call
  Futu API or place orders directly.
---

# Algo Strategy Agent

Implement trading algorithms in the **strategy layer only**. Strategies produce `Signal` objects; the engine handles risk checks and order execution.

## Golden Rules

1. **Output signals only** — never call `place_order` or Futu API
2. **Declare data needs** via `DataSubscription` (intervals + tick)
3. **Parameters in YAML** — `config/strategies/<name>.yaml`, not hardcoded
4. **Register** new strategies in `src/strategy/registry.py`
5. **Test on SIMULATE** before any live discussion

## LLM-Modifiable Files

```
src/strategies/<strategy_name>.py    # Strategy implementation
config/strategies/<strategy_name>.yaml
src/strategy/registry.py           # Add one line to register
```

## Do NOT Modify

- `src/broker/` — execution layer
- `src/risk/guard.py` — unless user explicitly requests risk changes
- `src/engine/` — unless user explicitly requests engine changes

## Strategy Template

```python
from src.strategy.base import BaseStrategy, StrategyContext
from src.models.signal import Signal, SignalSide
from src.models.market import Bar, Tick
from src.data.subscription import DataSubscription

class MyStrategy(BaseStrategy):
    name = "my_strategy"

    def __init__(self, params: dict):
        super().__init__(params)
        self.subscription = DataSubscription(
            symbols=params.get("symbols", []),
            intervals=[params.get("interval", "1d")],
            tick=params.get("tick", False),
        )

    def on_start(self, ctx: StrategyContext) -> None:
        pass

    def on_bar(self, bar: Bar, interval: str) -> list[Signal]:
        return []

    def on_tick(self, tick: Tick) -> list[Signal]:
        return []

    def on_stop(self, ctx: StrategyContext) -> None:
        pass
```

## DataSubscription Guide

| Strategy type | intervals | tick |
|---------------|-----------|------|
| Daily swing | `["1d"]` | `False` |
| Intraday | `["1m"]` | `False` |
| Multi-timeframe | `["1d", "1m"]` | `False` |
| Scalping | `[]` | `True` |
| Hybrid | `["1d"]` | `True` |

## Signal Format

```python
Signal(
    symbol="HK.00700",
    side=SignalSide.BUY,
    qty=100,
    price=350.0,          # required for LIMIT
    reason="SMA fast crossed above slow",
)
```

## Registration

Add to `src/strategy/registry.py`:

```python
STRATEGY_REGISTRY = {
    "my_strategy": MyStrategy,
}
```

## YAML Config

```yaml
name: my_strategy
market: HK
symbols: [HK.00700]
params:
  interval: "1d"
  fast_period: 10
  slow_period: 30
  qty: 100
```

## Runner Selection

| Data need | CLI command |
|-----------|-------------|
| Daily K | `python scripts/run_paper.py --strategy X --mode daily` |
| 1-minute | `python scripts/run_paper.py --strategy X --mode intraday --data 1m` |
| Tick | `python scripts/run_tick.py --strategy X` |

Tick strategies **must** use `run_tick.py` (separate process, stricter rate limits).

## Review Checklist

When reviewing LLM-generated strategy code:

- [ ] Extends `BaseStrategy`
- [ ] `subscription` matches `on_bar` / `on_tick` usage
- [ ] No direct Futu imports
- [ ] Parameters from `self.params`, not magic numbers
- [ ] Signals include `reason` for debugging
- [ ] Handles insufficient bar history gracefully
- [ ] Registered in registry + yaml exists

## Examples

See [examples.md](examples.md) for SMA crossover and tick scaffold patterns.
