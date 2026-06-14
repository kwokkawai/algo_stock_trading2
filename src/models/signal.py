from dataclasses import dataclass
from enum import Enum
from typing import Literal


class SignalSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Signal:
    symbol: str
    side: SignalSide
    qty: int
    order_type: Literal["LIMIT", "MARKET"] = "LIMIT"
    price: float | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        if self.order_type == "LIMIT" and self.price is None:
            raise ValueError(f"LIMIT order requires price: {self.symbol}")
