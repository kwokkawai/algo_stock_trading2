#!/usr/bin/env python3
"""Run strategy on paper (simulate) trading."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._cli import apply_env_override, base_parser, confirm_real_trading, setup_logging


def main() -> None:
    parser = base_parser("Run strategy on paper/simulate trading")
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
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required with --env real",
    )
    args = parser.parse_args()

    setup_logging(args.log_level)

    if args.env == "real":
        if not args.confirm or not confirm_real_trading():
            print("Aborted: real trading requires --confirm and YES prompt")
            return
        args.env = "real"
    else:
        args.env = "simulate"

    from src.config import load_settings
    from src.engine.runner import Engine

    settings = apply_env_override(load_settings(), args.env)
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
