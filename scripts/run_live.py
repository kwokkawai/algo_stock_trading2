#!/usr/bin/env python3
"""Run strategy on live (real) trading."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._cli import apply_env_override, base_parser, confirm_real_trading, setup_logging


def main() -> None:
    parser = base_parser("Run strategy on LIVE trading")
    parser.add_argument(
        "--mode",
        default="daily",
        choices=["daily", "intraday"],
        help="Runner mode",
    )
    parser.add_argument("--data", default=None, choices=["1d", "1m"])
    parser.add_argument(
        "--confirm",
        action="store_true",
        required=True,
        help="Required flag to enable live trading",
    )
    args = parser.parse_args()

    setup_logging(args.log_level)

    if not confirm_real_trading():
        print("Aborted.")
        return

    from src.config import load_settings
    from src.engine.runner import Engine

    settings = apply_env_override(load_settings(), "real")
    interval = args.data or ("1m" if args.mode == "intraday" else None)

    engine = Engine(
        strategy_name=args.strategy,
        mode=args.mode,
        market=args.market,
        settings=settings,
        interval_override=interval,
    )
    engine.run(once=False)


if __name__ == "__main__":
    main()
