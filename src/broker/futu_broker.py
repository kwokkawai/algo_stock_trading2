"""Futu OpenAPI broker adapter for Futu HK accounts."""

from __future__ import annotations

import logging
import os
from typing import Any

from src.models.order import (
    AccountInfo,
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderType,
    Position,
)

logger = logging.getLogger(__name__)

MARKET_PREFIX = {"HK": "HK", "US": "US"}


class FutuBroker:
    """Wraps futu-api trade context for HK/US order execution."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config
        broker_cfg = config.get("broker", {})
        trading_cfg = config.get("trading", {})

        self._host = broker_cfg.get("host", "127.0.0.1")
        self._port = broker_cfg.get("port", 11111)
        self._security_firm_name = broker_cfg.get("security_firm", "FUTUSECURITIES")
        self._env_name = trading_cfg.get("env", "simulate")
        self._trd_ctx = None
        self._quote_ctx = None

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "FutuBroker":
        return cls(config)

    @property
    def is_real(self) -> bool:
        return self._env_name == "real"

    def _import_futu(self):
        import futu as ft

        return ft

    def _security_firm(self, ft):
        firm_map = {
            "FUTUSECURITIES": ft.SecurityFirm.FUTUSECURITIES,
            "FUTUINC": ft.SecurityFirm.FUTUINC,
        }
        return firm_map.get(self._security_firm_name, ft.SecurityFirm.FUTUSECURITIES)

    def _trd_env(self, ft):
        return ft.TrdEnv.REAL if self.is_real else ft.TrdEnv.SIMULATE

    def _trd_market(self, ft, symbol: str):
        if symbol.startswith("US."):
            return ft.TrdMarket.US
        return ft.TrdMarket.HK

    def connect(self) -> None:
        ft = self._import_futu()
        self._trd_ctx = ft.OpenSecTradeContext(
            filter_trdmarket=ft.TrdMarket.HK,
            host=self._host,
            port=self._port,
            security_firm=self._security_firm(ft),
        )
        self._quote_ctx = ft.OpenQuoteContext(host=self._host, port=self._port)
        logger.info("Connected to OpenD at %s:%s (env=%s)", self._host, self._port, self._env_name)

    def disconnect(self) -> None:
        if self._trd_ctx:
            self._trd_ctx.close()
            self._trd_ctx = None
        if self._quote_ctx:
            self._quote_ctx.close()
            self._quote_ctx = None
        logger.info("Disconnected from OpenD")

    @property
    def quote_context(self):
        if self._quote_ctx is None:
            raise RuntimeError("Broker not connected. Call connect() first.")
        return self._quote_ctx

    def unlock(self) -> None:
        if not self.is_real:
            logger.info("Skipping unlock for simulate env")
            return

        password = os.environ.get("FUTU_TRADE_PASSWORD")
        if not password:
            raise RuntimeError("FUTU_TRADE_PASSWORD env var required for real trading")

        ft = self._import_futu()
        ret, data = self._trd_ctx.unlock_trade(password)
        if ret != ft.RET_OK:
            raise RuntimeError(f"unlock_trade failed: {data}")
        logger.info("Trading unlocked")

    def place_order(self, request: OrderRequest) -> OrderResult:
        ft = self._import_futu()
        trd_side = ft.TrdSide.BUY if request.side == OrderSide.BUY else ft.TrdSide.SELL
        order_type = (
            ft.OrderType.NORMAL
            if request.order_type == OrderType.LIMIT
            else ft.OrderType.MARKET
        )

        kwargs: dict[str, Any] = {
            "price": request.price or 0.0,
            "qty": request.qty,
            "code": request.symbol,
            "trd_side": trd_side,
            "order_type": order_type,
            "trd_env": self._trd_env(ft),
        }

        ret, data = self._trd_ctx.place_order(**kwargs)
        if ret != ft.RET_OK:
            logger.error("place_order failed: %s", data)
            return OrderResult(success=False, message=str(data))

        order_id = str(data["order_id"].iloc[0]) if not data.empty else None
        logger.info(
            "Order placed: %s %s x%d @ %s (id=%s) — %s",
            request.side.value,
            request.symbol,
            request.qty,
            request.price,
            order_id,
            request.reason,
        )
        return OrderResult(success=True, order_id=order_id, raw=data.to_dict() if not data.empty else {})

    def cancel_order(self, order_id: str) -> bool:
        ft = self._import_futu()
        ret, data = self._trd_ctx.modify_order(
            ft.ModifyOrderOp.CANCEL,
            order_id,
            0,
            0,
            trd_env=self._trd_env(ft),
        )
        if ret != ft.RET_OK:
            logger.error("cancel_order failed: %s", data)
            return False
        return True

    def get_positions(self, market: str | None = None) -> list[Position]:
        ft = self._import_futu()
        ret, data = self._trd_ctx.position_list_query(trd_env=self._trd_env(ft))
        if ret != ft.RET_OK or data is None or data.empty:
            return []

        positions: list[Position] = []
        for _, row in data.iterrows():
            code = str(row.get("code", ""))
            if market and not code.startswith(f"{market}."):
                continue
            positions.append(
                Position(
                    symbol=code,
                    qty=int(row.get("qty", 0)),
                    cost_price=float(row.get("cost_price", 0)),
                    market_value=float(row.get("market_val", 0)),
                )
            )
        return positions

    def get_account_info(self) -> AccountInfo:
        ft = self._import_futu()
        ret, data = self._trd_ctx.accinfo_query(trd_env=self._trd_env(ft))
        if ret != ft.RET_OK or data is None or data.empty:
            return AccountInfo(total_assets=0, cash=0, market_val=0, env=self._env_name)

        row = data.iloc[0]
        return AccountInfo(
            total_assets=float(row.get("total_assets", 0)),
            cash=float(row.get("cash", 0)),
            market_val=float(row.get("market_val", 0)),
            env=self._env_name,
        )
