#!/usr/bin/env python3
"""Performance report from SQLite journal — day / week / month."""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._cli import load_trading_settings, report_parser, setup_logging


def main() -> int:
    parser = report_parser("Performance report from trade journal")
    args = parser.parse_args()
    setup_logging(args.log_level)

    from src.journal.reporter import PerformanceReporter, format_report_text
    from src.journal.store import JournalStore

    settings = load_trading_settings()
    journal = JournalStore.from_settings(settings)
    reporter = PerformanceReporter(journal)

    anchor = datetime.fromisoformat(args.date) if args.date else None
    report = reporter.build(args.period, strategy_name=args.strategy, anchor=anchor)
    text = format_report_text(report)

    if args.export == "json":
        print(json.dumps(report.to_dict(), indent=2))
    elif args.export == "csv":
        path = Path(args.output or f"report_{report.label}.csv")
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(report.to_dict().keys()))
            writer.writeheader()
            writer.writerow(report.to_dict())
        print(f"Wrote {path}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
