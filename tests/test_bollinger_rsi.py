from src.models.signal import SignalSide
from src.strategies.bollinger_rsi import BollingerRsiStrategy
from tests.strategy_helpers import make_bars


def test_bollinger_rsi_buy_on_oversold():
    params = {
        "symbols": ["HK.00700"],
        "interval": "1d",
        "bb_period": 5,
        "bb_std": 2.0,
        "rsi_period": 5,
        "rsi_buy": 40,
        "rsi_sell": 70,
        "qty": 100,
    }
    strategy = BollingerRsiStrategy(params)
    # Flat then sharp drop → close at/below lower band + low RSI
    closes = [100, 100, 100, 100, 100, 20]
    signals = []
    for bar in make_bars(closes):
        signals.extend(strategy.on_bar(bar, "1d"))
    buys = [s for s in signals if s.side == SignalSide.BUY]
    assert len(buys) >= 1
