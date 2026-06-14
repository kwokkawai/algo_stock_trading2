#!/usr/bin/env python3
"""Run strategy on live (real) trading — blocked while paper_only is enabled."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._cli import confirm_real_trading, load_trading_settings, paper_parser, setup_logging


def main() -> int:
    parser = paper_parser("Run strategy on LIVE trading (disabled until paper_only is false)")
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

    from src.trading_policy import PaperOnlyError, assert_paper_trade_allowed

    settings = load_trading_settings()
    try:
        assert_paper_trade_allowed(settings, "run live trading")
    except PaperOnlyError as exc:
        print(f"BLOCKED: {exc}")
        return 1

    if not confirm_real_trading():
        print("Aborted.")
        return 1

    from src.engine.runner import Engine
    from src.trading_policy import REAL_ENV

    settings = dict(settings)
    trading = dict(settings.get("trading", {}))
    trading["env"] = REAL_ENV
    settings["trading"] = trading

    interval = args.data or ("1m" if args.mode == "intraday" else None)

    engine = Engine(
        strategy_name=args.strategy,
        mode=args.mode,
        market=args.market,
        settings=settings,
        interval_override=interval,
    )
    engine.run(once=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
