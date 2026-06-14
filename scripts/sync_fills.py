#!/usr/bin/env python3
"""Sync Futu orders and deal fills into the local SQLite journal."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._cli import load_trading_settings, setup_logging, sync_parser


def main() -> int:
    parser = sync_parser("Sync Futu orders/deals into SQLite journal")
    args = parser.parse_args()
    setup_logging(args.log_level)

    from src.broker.futu_broker import FutuBroker
    from src.journal.store import JournalStore
    from src.journal.sync import sync_fills

    settings = load_trading_settings()
    journal = JournalStore.from_settings(settings)
    broker = FutuBroker.from_config(settings)

    try:
        broker.connect()
        if broker.is_real:
            broker.unlock()
        orders, deals = sync_fills(
            broker,
            journal,
            start=args.start or "",
            end=args.end or "",
            include_history=args.history,
        )
        print(f"Synced {orders} orders, {deals} deals → {journal.db_path}")
    finally:
        broker.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
