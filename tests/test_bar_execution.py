"""Tests for bar-level execution deduplication."""

from datetime import datetime

from src.engine.bar_execution import BarExecutionGate


def test_allows_first_bar_then_blocks_duplicate():
    gate = BarExecutionGate()
    ts = datetime(2026, 6, 15, 10, 1)
    assert gate.should_execute("HK.00700", ts) is True
    assert gate.should_execute("HK.00700", ts) is False


def test_new_bar_allowed():
    gate = BarExecutionGate()
    assert gate.should_execute("HK.00700", datetime(2026, 6, 15, 10, 1)) is True
    assert gate.should_execute("HK.00700", datetime(2026, 6, 15, 10, 2)) is True


def test_symbols_independent():
    gate = BarExecutionGate()
    ts = datetime(2026, 6, 15, 10, 1)
    assert gate.should_execute("HK.00700", ts) is True
    assert gate.should_execute("HK.09988", ts) is True
