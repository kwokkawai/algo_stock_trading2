from src.models.signal import SignalSide
from src.strategies.momentum_rotation import MomentumRotationStrategy
from tests.strategy_helpers import make_bars


def test_momentum_rotation_picks_leader():
    symbols = ["HK.A", "HK.B"]
    params = {
        "symbols": symbols,
        "interval": "1d",
        "lookback": 2,
        "top_n": 1,
        "qty": 100,
    }
    strategy = MomentumRotationStrategy(params)

    # HK.A flat, HK.B strong uptrend
    a_closes = [10, 10, 10, 10]
    b_closes = [10, 11, 12, 13]

    signals = []
    for bar in make_bars(a_closes, symbol="HK.A"):
        signals.extend(strategy.on_bar(bar, "1d"))
    for bar in make_bars(b_closes, symbol="HK.B"):
        signals.extend(strategy.on_bar(bar, "1d"))

    buys = [s for s in signals if s.side == SignalSide.BUY]
    assert len(buys) == 1
    assert buys[0].symbol == "HK.B"
