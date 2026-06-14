from dataclasses import dataclass
from datetime import datetime


@dataclass
class Bar:
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime
    interval: str = "1d"


@dataclass
class Tick:
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    bid: float | None = None
    ask: float | None = None
