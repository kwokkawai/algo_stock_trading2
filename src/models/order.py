from dataclasses import dataclass
from enum import Enum
from typing import Literal


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


@dataclass
class OrderRequest:
    symbol: str
    side: OrderSide
    qty: int
    order_type: OrderType = OrderType.LIMIT
    price: float | None = None
    reason: str = ""


@dataclass
class OrderResult:
    success: bool
    order_id: str | None = None
    message: str = ""
    raw: dict | None = None


@dataclass
class Position:
    symbol: str
    qty: int
    cost_price: float
    market_value: float = 0.0


@dataclass
class AccountInfo:
    total_assets: float
    cash: float
    market_val: float
    env: Literal["simulate", "real"] = "simulate"


@dataclass
class OrderRecord:
    order_id: str
    symbol: str
    side: OrderSide
    qty: int
    price: float | None
    order_status: str
    dealt_qty: int
    dealt_avg_price: float | None
    create_time: str
    updated_time: str
    env: Literal["simulate", "real"] = "simulate"
    strategy_name: str | None = None
    reason: str | None = None


@dataclass
class DealRecord:
    deal_id: str
    order_id: str
    symbol: str
    side: OrderSide
    qty: int
    price: float
    create_time: str
    env: Literal["simulate", "real"] = "simulate"
