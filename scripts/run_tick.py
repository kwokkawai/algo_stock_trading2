#!/usr/bin/env python3
"""Run tick strategy on paper/simulate trading (separate process)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._cli import apply_env_override, base_parser, confirm_real_trading, setup_logging


def main() -> None:
    parser = base_parser("Run tick strategy (separate runner with stricter rate limits)")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run briefly then exit (5s test)",
    )
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()

    setup_logging(args.log_level)

    if args.env == "real":
        if not args.confirm or not confirm_real_trading():
            print("Aborted: real tick trading requires --confirm and YES prompt")
            return

    from src.config import load_settings
    from src.engine.runner import Engine

    settings = apply_env_override(load_settings(), args.env)
    engine = Engine(
        strategy_name=args.strategy,
        mode="tick",
        market=args.market,
        settings=settings,
    )
    engine.run(once=args.once)


if __name__ == "__main__":
    main()
