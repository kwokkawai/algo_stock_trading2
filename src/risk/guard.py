"""Risk guard — validates signals before order execution."""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field

from src.models.order import OrderRequest, OrderSide, OrderType, Position
from src.models.signal import Signal, SignalSide

logger = logging.getLogger(__name__)


@dataclass
class RiskConfig:
    max_notional_per_order: float = 50000
    max_position_pct: float = 0.2
    daily_loss_limit: float = 10000
    signal_cooldown_seconds: float = 60
    tick_max_orders_per_minute: int = 10
    allowed_symbols: dict[str, list[str]] = field(default_factory=dict)


class RiskGuard:
    def __init__(self, config: RiskConfig, tick_mode: bool = False) -> None:
        self._config = config
        self._tick_mode = tick_mode
        self._last_signal_time: dict[str, float] = {}
        self._order_timestamps: deque[float] = deque()
        self._daily_pnl: float = 0.0
        self._rejected_count = 0

    @classmethod
    def from_settings(cls, settings: dict, tick_mode: bool = False) -> "RiskGuard":
        risk = settings.get("risk", {})
        return cls(
            RiskConfig(
                max_notional_per_order=risk.get("max_notional_per_order", 50000),
                max_position_pct=risk.get("max_position_pct", 0.2),
                daily_loss_limit=risk.get("daily_loss_limit", 10000),
                signal_cooldown_seconds=risk.get("signal_cooldown_seconds", 60),
                tick_max_orders_per_minute=risk.get("tick_max_orders_per_minute", 10),
                allowed_symbols=risk.get("allowed_symbols", {}),
            ),
            tick_mode=tick_mode,
        )

    def is_halted(self) -> bool:
        return self._daily_pnl <= -self._config.daily_loss_limit

    def validate(
        self,
        signals: list[Signal],
        positions: list[Position] | None = None,
        account_total: float = 0,
    ) -> list[OrderRequest]:
        if self.is_halted():
            logger.warning("Risk halt: daily loss limit reached")
            return []

        positions = positions or []
        approved: list[OrderRequest] = []

        for signal in signals:
            reason = self._check_signal(signal, positions, account_total)
            if reason:
                logger.warning("Signal rejected [%s]: %s", signal.symbol, reason)
                self._rejected_count += 1
                continue

            self._record_order()
            self._last_signal_time[signal.symbol] = time.time()

            approved.append(
                OrderRequest(
                    symbol=signal.symbol,
                    side=OrderSide(signal.side.value),
                    qty=signal.qty,
                    order_type=OrderType(signal.order_type),
                    price=signal.price,
                    reason=signal.reason,
                )
            )

        return approved

    def _check_signal(
        self,
        signal: Signal,
        positions: list[Position],
        account_total: float,
    ) -> str | None:
        if not self._is_symbol_allowed(signal.symbol):
            return "symbol not in whitelist"

        if signal.side == SignalSide.SELL:
            pos = next((p for p in positions if p.symbol == signal.symbol), None)
            held = pos.qty if pos else 0
            if held < signal.qty:
                return f"insufficient position to sell (have {held}, need {signal.qty})"

        notional = (signal.price or 0) * signal.qty
        if signal.order_type == "LIMIT" and notional > self._config.max_notional_per_order:
            return f"notional {notional:.0f} exceeds max {self._config.max_notional_per_order}"

        if self._tick_mode and not self._tick_rate_ok():
            return "tick rate limit exceeded"

        cooldown = self._config.signal_cooldown_seconds
        last = self._last_signal_time.get(signal.symbol, 0)
        if time.time() - last < cooldown:
            return f"cooldown ({cooldown}s) not elapsed"

        if account_total > 0:
            pos = next((p for p in positions if p.symbol == signal.symbol), None)
            current_val = (pos.market_value if pos else 0) + notional
            if current_val / account_total > self._config.max_position_pct:
                return f"position would exceed {self._config.max_position_pct:.0%} of account"

        return None

    def _is_symbol_allowed(self, symbol: str) -> bool:
        if not self._config.allowed_symbols:
            return True
        for symbols in self._config.allowed_symbols.values():
            if symbol in symbols:
                return True
        return False

    def _tick_rate_ok(self) -> bool:
        now = time.time()
        while self._order_timestamps and now - self._order_timestamps[0] > 60:
            self._order_timestamps.popleft()
        return len(self._order_timestamps) < self._config.tick_max_orders_per_minute

    def _record_order(self) -> None:
        self._order_timestamps.append(time.time())
