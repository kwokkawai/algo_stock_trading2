"""Bar data feed — wraps Futu quote context for K-line data."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable

from src.data.subscription import INTERVAL_TO_SUBTYPE, DataSubscription
from src.models.market import Bar

logger = logging.getLogger(__name__)

BarHandler = Callable[[Bar], None]


class BarFeed:
    """Fetches and dispatches K-line bars from Futu OpenAPI."""

    def __init__(self, quote_ctx, subscription: DataSubscription) -> None:
        self._quote_ctx = quote_ctx
        self._subscription = subscription
        self._handlers: list[BarHandler] = []

    def add_handler(self, handler: BarHandler) -> None:
        self._handlers.append(handler)

    def subscribe(self) -> None:
        import futu as ft

        sub_types = []
        for interval in self._subscription.intervals:
            subtype_name = INTERVAL_TO_SUBTYPE.get(interval)
            if subtype_name and hasattr(ft.SubType, subtype_name):
                sub_types.append(getattr(ft.SubType, subtype_name))

        if not sub_types:
            logger.warning("No bar intervals to subscribe")
            return

        for symbol in self._subscription.symbols:
            ret, msg = self._quote_ctx.subscribe([symbol], sub_types)
            if ret != ft.RET_OK:
                logger.error("Subscribe failed for %s: %s", symbol, msg)

    def fetch_latest_bars(self, interval: str, count: int = 100) -> list[Bar]:
        """Pull recent K-lines via get_cur_kline (polling mode for scaffold)."""
        import futu as ft

        subtype_name = INTERVAL_TO_SUBTYPE.get(interval)
        if not subtype_name:
            return []

        ktype = getattr(ft.KLType, subtype_name, None)
        if ktype is None:
            return []

        bars: list[Bar] = []
        for symbol in self._subscription.symbols:
            ret, data = self._quote_ctx.get_cur_kline(symbol, count, ktype)
            if ret != ft.RET_OK or data is None or data.empty:
                logger.warning("get_cur_kline failed for %s: %s", symbol, data)
                continue

            for _, row in data.iterrows():
                bars.append(
                    Bar(
                        symbol=symbol,
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row.get("volume", 0)),
                        timestamp=_parse_time(row.get("time_key", "")),
                        interval=interval,
                    )
                )
        return bars

    def dispatch_bar(self, bar: Bar) -> None:
        for handler in self._handlers:
            handler(bar)


def _parse_time(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace(" ", "T"))
        except ValueError:
            pass
    return datetime.now()
