#!/usr/bin/env python3
"""Run tick strategy on paper/simulate account only (separate process)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._cli import load_trading_settings, paper_parser, setup_logging


def main() -> None:
    parser = paper_parser("Run tick strategy on Futu paper account (stricter rate limits)")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run briefly then exit (5s test)",
    )
    args = parser.parse_args()

    setup_logging(args.log_level)

    from src.engine.runner import Engine

    settings = load_trading_settings()
    engine = Engine(
        strategy_name=args.strategy,
        mode="tick",
        market=args.market,
        settings=settings,
    )
    engine.run(once=args.once)


if __name__ == "__main__":
    main()
