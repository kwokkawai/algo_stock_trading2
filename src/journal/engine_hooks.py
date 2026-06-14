"""Engine integration — journal hooks."""

from __future__ import annotations

import logging

from src.broker.futu_broker import FutuBroker
from src.journal.store import JournalStore
from src.models.signal import Signal

logger = logging.getLogger(__name__)


def journal_enabled(settings: dict) -> bool:
    return settings.get("journal", {}).get("enabled", True)


def open_journal(settings: dict) -> JournalStore | None:
    if not journal_enabled(settings):
        return None
    try:
        return JournalStore.from_settings(settings)
    except Exception as exc:
        logger.warning("Journal disabled due to init error: %s", exc)
        return None


def record_account_snapshot(
    broker: FutuBroker,
    journal: JournalStore | None,
    *,
    snapshot_type: str,
    strategy_name: str | None = None,
    run_id: str | None = None,
    market: str | None = None,
) -> None:
    if journal is None:
        return
    account = broker.get_account_info()
    positions = broker.get_positions(market=market)
    journal.record_snapshot(
        account,
        positions,
        snapshot_type=snapshot_type,
        strategy_name=strategy_name,
        run_id=run_id,
    )


def log_signals(
    journal: JournalStore | None,
    signals: list[Signal],
    *,
    strategy_name: str,
    run_id: str | None,
) -> None:
    if journal is None:
        return
    for signal in signals:
        journal.record_signal(signal, strategy_name=strategy_name, run_id=run_id)
