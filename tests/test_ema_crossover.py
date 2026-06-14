from src.models.signal import SignalSide
from src.strategies.ema_crossover import EmaCrossoverStrategy
from tests.strategy_helpers import make_bars


def test_ema_buy_on_cross():
    params = {
        "symbols": ["HK.00700"],
        "interval": "1d",
        "fast_period": 2,
        "slow_period": 3,
        "qty": 100,
    }
    strategy = EmaCrossoverStrategy(params)
    closes = [10, 9, 8, 9, 10, 12]
    signals = []
    for bar in make_bars(closes):
        signals.extend(strategy.on_bar(bar, "1d"))
    assert any(s.side == SignalSide.BUY for s in signals)
