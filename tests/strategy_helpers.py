from datetime import datetime

from src.models.market import Bar


def make_bars(closes: list[float], symbol: str = "HK.00700", interval: str = "1d") -> list[Bar]:
    bars = []
    for i, close in enumerate(closes):
        bars.append(
            Bar(
                symbol=symbol,
                open=close,
                high=close + 1,
                low=close - 1,
                close=close,
                volume=1000,
                timestamp=datetime(2026, 1, i + 1),
                interval=interval,
            )
        )
    return bars
