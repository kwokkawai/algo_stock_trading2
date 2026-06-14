import pytest

from src.models.signal import Signal, SignalSide


def test_limit_signal_requires_price():
    with pytest.raises(ValueError, match="LIMIT order requires price"):
        Signal(symbol="HK.00700", side=SignalSide.BUY, qty=100)


def test_limit_signal_ok():
    sig = Signal(symbol="HK.00700", side=SignalSide.BUY, qty=100, price=350.0)
    assert sig.side == SignalSide.BUY
    assert sig.price == 350.0
