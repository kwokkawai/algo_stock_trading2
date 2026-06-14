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

    def run(self, once: bool = False) -> None:
        if self._mode == "tick":
            self._run_tick(once=once)
        else:
            self._run_bar(once=once)

    def _run_bar(self, once: bool = False) -> None:
        self._broker.connect()
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
            self._strategy.on_stop(self._ctx)
            self._broker.disconnect()

    def _run_tick(self, once: bool = False) -> None:
        self._broker.connect()
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
            self._strategy.on_stop(self._ctx)
            self._broker.disconnect()

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

        account = self._broker.get_account_info()
        orders = self._risk.validate(
            signals,
            positions=self._ctx.positions,
            account_total=account.total_assets,
        )
        for order in orders:
            result = self._broker.place_order(order)
            if not result.success:
                logger.error("Order failed: %s", result.message)
