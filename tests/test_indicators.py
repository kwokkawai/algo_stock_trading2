from src.strategies.indicators import bollinger_bands, ema_series, rsi


def test_ema_series():
    closes = [1, 2, 3, 4, 5]
    series = ema_series(closes, 3)
    assert series[0] is None
    assert series[1] is None
    assert series[2] is not None


def test_rsi_oversold():
    closes = [10.0] + [9.0 - i * 0.1 for i in range(20)]
    val = rsi(closes, 14)
    assert val is not None
    assert val < 50


def test_bollinger_bands():
    closes = [float(i) for i in range(1, 25)]
    bands = bollinger_bands(closes, 20, 2.0)
    assert bands is not None
    lower, middle, upper = bands
    assert lower < middle < upper
