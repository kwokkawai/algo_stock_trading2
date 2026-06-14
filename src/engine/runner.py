"""Trading engine — orchestrates data feed, strategy, risk, and broker."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Literal

from src.broker.futu_broker import FutuBroker
from src.config import load_settings, load_strategy_config
from src.data.bar_feed import BarFeed
from src.data.tick_feed import TickFeed
from src.journal.engine_hooks import (
    log_signals,
    open_journal,
    record_account_snapshot,
)
from src.journal.sync import sync_fills
from src.risk.guard import RiskGuard
from src.strategy.base import StrategyContext
from src.strategy.registry import get_strategy

logger = logging.getLogger(__name__)

RunnerMode = Literal["daily", "intraday", "tick"]


class Engine:
    def __init__(
        self,
        strategy_name: str,
        mode: RunnerMode = "daily",
        market: str = "HK",
        settings: dict | None = None,
        interval_override: str | None = None,
    ) -> None:
        self._settings = settings or load_settings()
        self._strategy_config = load_strategy_config(strategy_name)
        self._mode = mode
        self._market = market

        params = self._strategy_config.get("params", {})
        params.setdefault("symbols", self._strategy_config.get("symbols", []))
        params.setdefault("market", self._strategy_config.get("market", market))
        if interval_override:
            params["interval"] = interval_override

        self._strategy = get_strategy(strategy_name, params)
        self._broker = FutuBroker.from_config(self._settings)
        self._risk = RiskGuard.from_settings(
            self._settings, tick_mode=(mode == "tick")
        )
        self._ctx = StrategyContext(
            params=params,
            market=self._strategy_config.get("market", market),
        )
        self._strategy_name = strategy_name
        self._journal = open_journal(self._settings)
        self._run_id: str | None = None

    def run(self, once: bool = False) -> None:
        if self._mode == "tick":
            self._run_tick(once=once)
        else:
            self._run_bar(once=once)

    def _run_bar(self, once: bool = False) -> None:
        self._broker.connect()
        self._begin_run()
        try:
            if self._broker.is_real:
                self._broker.unlock()

            self._strategy.on_start(self._ctx)
            bar_feed = BarFeed(self._broker.quote_context, self._strategy.subscription)
            bar_feed.subscribe()

            interval = self._strategy.params.get("interval", "1d")
            sleep_seconds = 60 if self._mode == "intraday" else 86400

            while True:
                if self._risk.is_halted():
                    logger.warning("Engine halted by risk guard")
                    break

                self._refresh_context()
                bars = bar_feed.fetch_latest_bars(interval)
                self._process_bars(bars, interval)

                if once:
                    break
                logger.info("Sleeping %ds until next poll...", sleep_seconds)
                time.sleep(sleep_seconds)

        finally:
            self._end_run()
            self._strategy.on_stop(self._ctx)
            self._broker.disconnect()

    def _run_tick(self, once: bool = False) -> None:
        self._broker.connect()
        self._begin_run()
        try:
            if self._broker.is_real:
                self._broker.unlock()

            self._strategy.on_start(self._ctx)
            tick_feed = TickFeed(self._broker.quote_context, self._strategy.subscription)
            tick_feed.subscribe()
            tick_feed.set_callback()

            tick_feed.add_handler(self._on_tick)

            if once:
                time.sleep(5)
                return

            logger.info("Tick engine running — Ctrl+C to stop")
            while not self._risk.is_halted():
                time.sleep(1)

        finally:
            self._end_run()
            self._strategy.on_stop(self._ctx)
            self._broker.disconnect()

    def _begin_run(self) -> None:
        if self._journal is None:
            return
        self._run_id = self._journal.new_run_id()
        self._journal.start_session(
            self._run_id,
            strategy_name=self._strategy_name,
            market=self._market,
            mode=self._mode,
            env=self._broker.env_name,
        )
        record_account_snapshot(
            self._broker,
            self._journal,
            snapshot_type="run_start",
            strategy_name=self._strategy_name,
            run_id=self._run_id,
            market=self._market,
        )

    def _end_run(self) -> None:
        if self._journal is None or self._run_id is None:
            return
        try:
            sync_fills(self._broker, self._journal)
        except Exception as exc:
            logger.warning("Fill sync failed: %s", exc)
        record_account_snapshot(
            self._broker,
            self._journal,
            snapshot_type="run_end",
            strategy_name=self._strategy_name,
            run_id=self._run_id,
            market=self._market,
        )
        self._journal.end_session(self._run_id)

    def _process_bars(self, bars, interval: str) -> None:
        """Warm up strategy on history; execute signals only on the latest bar per symbol."""
        by_symbol: dict[str, list] = defaultdict(list)
        for bar in bars:
            by_symbol[bar.symbol].append(bar)

        for symbol_bars in by_symbol.values():
            for bar in symbol_bars[:-1]:
                self._strategy.on_bar(bar, interval)
            if symbol_bars:
                signals = self._strategy.on_bar(symbol_bars[-1], interval)
                self._execute_signals(signals)

    def _on_tick(self, tick) -> None:
        self._refresh_context()
        signals = self._strategy.on_tick(tick)
        self._execute_signals(signals)

    def _refresh_context(self) -> None:
        self._ctx.positions = self._broker.get_positions(market=self._market)

    def _execute_signals(self, signals) -> None:
        if not signals:
            return

        log_signals(
            self._journal,
            signals,
            strategy_name=self._strategy_name,
            run_id=self._run_id,
        )

        account = self._broker.get_account_info()
        result = self._risk.validate(
            signals,
            positions=self._ctx.positions,
            account_total=account.total_assets,
        )

        if self._journal:
            for signal, reason in result.rejected:
                self._journal.record_risk_rejected(
                    signal,
                    reason,
                    strategy_name=self._strategy_name,
                    run_id=self._run_id,
                )

        for order in result.approved:
            placed = self._broker.place_order(order)
            if not placed.success:
                logger.error("Order failed: %s", placed.message)
                if self._journal:
                    self._journal.record_order_failed(
                        symbol=order.symbol,
                        side=order.side.value,
                        qty=order.qty,
                        price=order.price,
                        reason=order.reason,
                        message=placed.message,
                        strategy_name=self._strategy_name,
                        run_id=self._run_id,
                    )
                continue
            if self._journal and placed.order_id:
                self._journal.record_order_submitted(
                    order_id=placed.order_id,
                    symbol=order.symbol,
                    side=order.side.value,
                    qty=order.qty,
                    price=order.price,
                    reason=order.reason,
                    env=self._broker.env_name,
                    strategy_name=self._strategy_name,
                    run_id=self._run_id,
                )
