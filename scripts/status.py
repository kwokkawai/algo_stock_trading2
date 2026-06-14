#!/usr/bin/env python3
"""Query account status, positions, and recent orders."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._cli import load_trading_settings, setup_logging, status_parser


def main() -> None:
    parser = status_parser("Query Futu paper/simulate account status")
    args = parser.parse_args()
    setup_logging(args.log_level)

    from src.broker.futu_broker import FutuBroker

    settings = load_trading_settings()
    broker = FutuBroker.from_config(settings)

    try:
        broker.connect()
        if broker.is_real:
            broker.unlock()

        account = broker.get_account_info()
        positions = broker.get_positions(market=args.market)

        print("\n=== Account ===")
        print(f"  Environment : {account.env}")
        print(f"  Total assets: {account.total_assets:,.2f}")
        print(f"  Cash        : {account.cash:,.2f}")
        print(f"  Market val  : {account.market_val:,.2f}")

        print(f"\n=== Positions ({args.market}) ===")
        if not positions:
            print("  (none)")
        for pos in positions:
            print(
                f"  {pos.symbol}: qty={pos.qty}, "
                f"cost={pos.cost_price:.2f}, mkt_val={pos.market_value:.2f}"
            )

    finally:
        broker.disconnect()


if __name__ == "__main__":
    main()
