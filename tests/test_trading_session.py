"""Tests for HK trading session helper."""

from datetime import datetime
from zoneinfo import ZoneInfo

from src.market.session import is_hk_trading_session, is_trading_session

HK = ZoneInfo("Asia/Hong_Kong")


def test_hk_weekday_morning_open():
    dt = datetime(2026, 6, 15, 10, 0, tzinfo=HK)  # Monday
    assert is_hk_trading_session(dt) is True


def test_hk_weekday_lunch_break():
    dt = datetime(2026, 6, 15, 12, 30, tzinfo=HK)
    assert is_hk_trading_session(dt) is False


def test_hk_weekday_afternoon_open():
    dt = datetime(2026, 6, 15, 14, 0, tzinfo=HK)
    assert is_hk_trading_session(dt) is True


def test_hk_weekend_closed():
    dt = datetime(2026, 6, 14, 10, 0, tzinfo=HK)  # Sunday
    assert is_hk_trading_session(dt) is False


def test_is_trading_session_hk():
    dt = datetime(2026, 6, 15, 10, 0, tzinfo=HK)
    assert is_trading_session("HK", dt) is True
