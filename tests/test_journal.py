"""Tests for SQLite journal store and performance reporter."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.journal.reporter import PerformanceReporter, format_report_text
from src.journal.store import JournalStore
from src.models.order import AccountInfo, DealRecord, OrderRecord, OrderSide, Position
from src.models.signal import Signal, SignalSide


@pytest.fixture
def journal(tmp_path):
    return JournalStore(tmp_path / "test.db", timezone_name="Asia/Hong_Kong")


def test_record_signal_and_rejection(journal: JournalStore):
    signal = Signal(symbol="HK.00700", side=SignalSide.BUY, qty=100, price=400.0, reason="test")
    journal.record_signal(signal, strategy_name="sma_crossover", run_id="run-1")
    journal.record_risk_rejected(signal, "cooldown", strategy_name="sma_crossover", run_id="run-1")

    assert journal.count_events("signal", strategy_name="sma_crossover") == 1
    assert journal.count_events("risk_rejected", strategy_name="sma_crossover") == 1


def test_order_and_deal_upsert(journal: JournalStore):
    journal.record_order_submitted(
        order_id="1001",
        symbol="HK.00700",
        side="BUY",
        qty=100,
        price=400.0,
        reason="SMA BUY",
        env="simulate",
        strategy_name="sma_crossover",
    )
    journal.upsert_orders(
        [
            OrderRecord(
                order_id="1001",
                symbol="HK.00700",
                side=OrderSide.BUY,
                qty=100,
                price=400.0,
                order_status="FILLED_ALL",
                dealt_qty=100,
                dealt_avg_price=399.5,
                create_time="2026-06-14 10:00:00",
                updated_time="2026-06-14 10:00:01",
                env="simulate",
                strategy_name="sma_crossover",
            )
        ]
    )
    journal.upsert_deals(
        [
            DealRecord(
                deal_id="d1",
                order_id="1001",
                symbol="HK.00700",
                side=OrderSide.BUY,
                qty=100,
                price=399.5,
                create_time="2026-06-14 10:00:01",
                env="simulate",
            )
        ]
    )
    deals = journal.fetch_deals(strategy_name="sma_crossover")
    assert len(deals) == 1
    assert deals[0]["price"] == 399.5


def test_snapshot_and_report(journal: JournalStore):
    tz = ZoneInfo("Asia/Hong_Kong")
    anchor = datetime(2026, 6, 14, 15, 0, tzinfo=tz)

    journal.record_snapshot(
        AccountInfo(total_assets=1_000_000, cash=1_000_000, market_val=0, env="simulate"),
        [],
        snapshot_type="eod",
        strategy_name="sma_crossover",
    )
    journal.record_snapshot(
        AccountInfo(total_assets=1_010_000, cash=900_000, market_val=110_000, env="simulate"),
        [Position(symbol="HK.00700", qty=100, cost_price=400, market_value=110_000)],
        snapshot_type="eod",
        strategy_name="sma_crossover",
    )

    reporter = PerformanceReporter(journal)
    report = reporter.build("day", strategy_name=None, anchor=anchor)
    text = format_report_text(report)

    assert report.end_assets == 1_010_000
    assert report.return_pct == pytest.approx(1.0)
    assert "Performance Report" in text


def test_local_date_bounds_week(journal: JournalStore):
    tz = ZoneInfo("Asia/Hong_Kong")
    anchor = datetime(2026, 6, 14, 12, 0, tzinfo=tz)  # Saturday
    start, end = journal.local_date_bounds("week", anchor=anchor)
    assert start < end
