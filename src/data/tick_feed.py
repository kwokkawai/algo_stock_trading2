"""Tick data feed — wraps Futu Ticker subscription."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable

from src.data.subscription import DataSubscription
from src.models.market import Tick

logger = logging.getLogger(__name__)

TickHandler = Callable[[Tick], None]


class TickFeed:
    """Dispatches tick-by-tick data from Futu OpenAPI."""

    def __init__(self, quote_ctx, subscription: DataSubscription) -> None:
        self._quote_ctx = quote_ctx
        self._subscription = subscription
        self._handlers: list[TickHandler] = []

    def add_handler(self, handler: TickHandler) -> None:
        self._handlers.append(handler)

    def subscribe(self) -> None:
        import futu as ft

        if not self._subscription.tick:
            return

        for symbol in self._subscription.symbols:
            ret, msg = self._quote_ctx.subscribe([symbol], [ft.SubType.TICKER])
            if ret != ft.RET_OK:
                logger.error("Tick subscribe failed for %s: %s", symbol, msg)

    def set_callback(self) -> None:
        """Register Futu push callback for tick data."""
        import futu as ft

        class _Handler(ft.TickerHandlerBase):
            def __init__(self, outer: TickFeed) -> None:
                super().__init__()
                self._outer = outer

            def on_recv_rsp(self, rsp_pb):
                ret, data = super().on_recv_rsp(rsp_pb)
                if ret != ft.RET_OK or data is None or data.empty:
                    return ft.RET_OK, data

                for _, row in data.iterrows():
                    tick = Tick(
                        symbol=str(row.get("code", "")),
                        price=float(row.get("price", 0)),
                        volume=float(row.get("volume", 0)),
                        timestamp=_parse_time(row.get("time", "")),
                    )
                    self._outer.dispatch_tick(tick)
                return ft.RET_OK, data

        self._quote_ctx.set_handler(_Handler(self))

    def dispatch_tick(self, tick: Tick) -> None:
        for handler in self._handlers:
            handler(tick)


def _parse_time(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace(" ", "T"))
        except ValueError:
            pass
    return datetime.now()
