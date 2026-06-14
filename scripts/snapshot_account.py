#!/usr/bin/env python3
"""Record end-of-day (or manual) account snapshot into the journal."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._cli import load_trading_settings, setup_logging, snapshot_parser


def main() -> int:
    parser = snapshot_parser("Record account balance and positions snapshot")
    args = parser.parse_args()
    setup_logging(args.log_level)

    from src.broker.futu_broker import FutuBroker
    from src.journal.engine_hooks import record_account_snapshot
    from src.journal.store import JournalStore

    settings = load_trading_settings()
    journal = JournalStore.from_settings(settings)
    broker = FutuBroker.from_config(settings)

    try:
        broker.connect()
        if broker.is_real:
            broker.unlock()
        record_account_snapshot(
            broker,
            journal,
            snapshot_type=args.type,
            strategy_name=args.strategy,
            market=args.market,
        )
        account = broker.get_account_info()
        print(f"Snapshot saved ({args.type}) — assets={account.total_assets:,.2f} → {journal.db_path}")
    finally:
        broker.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
