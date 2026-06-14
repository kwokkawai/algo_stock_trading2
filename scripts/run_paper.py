#!/usr/bin/env python3
"""Run strategy on paper (simulate) trading only."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._cli import load_trading_settings, paper_parser, setup_logging


def main() -> None:
    parser = paper_parser("Run strategy on Futu paper/simulate account only")
    parser.add_argument(
        "--mode",
        default="daily",
        choices=["daily", "intraday"],
        help="Runner mode: daily (1d bars) or intraday (1m bars)",
    )
    parser.add_argument(
        "--data",
        default=None,
        choices=["1d", "1m"],
        help="Override bar interval (default: from strategy yaml)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one iteration then exit (useful for testing)",
    )
    args = parser.parse_args()

    setup_logging(args.log_level)

    from src.engine.runner import Engine

    settings = load_trading_settings()
    interval = args.data or ("1m" if args.mode == "intraday" else None)

    engine = Engine(
        strategy_name=args.strategy,
        mode=args.mode,
        market=args.market,
        settings=settings,
        interval_override=interval,
    )
    engine.run(once=args.once)


if __name__ == "__main__":
    main()
