from src.models.signal import SignalSide
from src.strategies.donchian_breakout import DonchianBreakoutStrategy
from tests.strategy_helpers import make_bars


def test_donchian_breakout_buy():
    params = {
        "symbols": ["HK.00700"],
        "interval": "1d",
        "entry_lookback": 3,
        "exit_lookback": 2,
        "qty": 100,
    }
    strategy = DonchianBreakoutStrategy(params)
    # Build range then breakout
    closes = [10, 10, 10, 10, 15]
    signals = []
    for bar in make_bars(closes):
        bar.high = bar.close + 0.5
        bar.low = bar.close - 0.5
        signals.extend(strategy.on_bar(bar, "1d"))
    buys = [s for s in signals if s.side == SignalSide.BUY]
    assert len(buys) >= 1
