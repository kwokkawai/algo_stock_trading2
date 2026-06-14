# Strategy Examples

## SMA Crossover (Daily / 1m)

File: `src/strategies/sma_crossover.py`

Logic:
1. Maintain price history per symbol
2. When fast SMA crosses above slow SMA → BUY
3. When fast SMA crosses below slow SMA → SELL

YAML params:
```yaml
params:
  interval: "1d"       # or "1m"
  fast_period: 10
  slow_period: 30
  qty: 100
```

Run:
```bash
python scripts/run_paper.py --strategy sma_crossover --mode daily --market HK
python scripts/run_paper.py --strategy sma_crossover --mode intraday --data 1m --market HK
```

## Tick Strategy Scaffold

For tick strategies, implement `on_tick` only and set `tick=True`:

```python
class TickScaffoldStrategy(BaseStrategy):
    name = "tick_scaffold"

    def __init__(self, params: dict):
        super().__init__(params)
        self.subscription = DataSubscription(
            symbols=params.get("symbols", []),
            tick=True,
        )
        self._last_price: dict[str, float] = {}

    def on_tick(self, tick: Tick) -> list[Signal]:
        # Example: placeholder — replace with real logic
        return []
```

Run:
```bash
python scripts/run_tick.py --strategy tick_scaffold --market HK
```

## Multi-Timeframe Pattern

Use `on_bar` with `interval` parameter to branch logic:

```python
def on_bar(self, bar: Bar, interval: str) -> list[Signal]:
    if interval == "1d":
        self._update_daily_trend(bar)
        return []
    if interval == "1m":
        return self._intraday_entries(bar)
    return []
```

Subscription:
```python
DataSubscription(symbols=["HK.00700"], intervals=["1d", "1m"])
```

## Common Pitfalls

1. **Not enough bars** — check `len(history) >= slow_period` before signaling
2. **Duplicate signals** — track last signal side per symbol
3. **Wrong runner** — tick strategy on `run_paper.py` won't receive ticks
4. **Missing registry entry** — strategy won't load without registry line
