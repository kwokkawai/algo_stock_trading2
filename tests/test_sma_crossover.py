from datetime import datetime

from src.models.market import Bar
from src.models.signal import SignalSide
from src.strategies.sma_crossover import SmaCrossoverStrategy


def _make_bars(closes: list[float], symbol: str = "HK.00700") -> list[Bar]:
    bars = []
    for i, close in enumerate(closes):
        bars.append(
            Bar(
                symbol=symbol,
                open=close,
                high=close,
                low=close,
                close=close,
                volume=1000,
                timestamp=datetime(2026, 1, i + 1),
                interval="1d",
            )
        )
    return bars


def test_sma_no_signal_before_slow_period():
    params = {
        "symbols": ["HK.00700"],
        "interval": "1d",
        "fast_period": 3,
        "slow_period": 5,
        "qty": 100,
    }
    strategy = SmaCrossoverStrategy(params)
    bars = _make_bars([10, 11, 12, 13, 14])
    signals = []
    for bar in bars:
        signals.extend(strategy.on_bar(bar, "1d"))
    assert signals == []


def test_sma_buy_on_golden_cross():
    params = {
        "symbols": ["HK.00700"],
        "interval": "1d",
        "fast_period": 2,
        "slow_period": 3,
        "qty": 100,
    }
    strategy = SmaCrossoverStrategy(params)
    # Declining then rising to trigger cross
    closes = [10, 9, 8, 9, 10, 12]
    all_signals = []
    for bar in _make_bars(closes):
        all_signals.extend(strategy.on_bar(bar, "1d"))

    buy_signals = [s for s in all_signals if s.side == SignalSide.BUY]
    assert len(buy_signals) >= 1
    assert buy_signals[0].symbol == "HK.00700"
