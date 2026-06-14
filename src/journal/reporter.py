"""Performance report generation from journal data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from src.journal.store import JournalStore

Period = Literal["day", "week", "month"]


@dataclass
class PerformanceReport:
    period: str
    label: str
    strategy_name: str | None
    start_assets: float | None
    end_assets: float | None
    return_pct: float | None
    cash_end: float | None
    market_val_end: float | None
    signal_count: int
    rejected_count: int
    orders_submitted: int
    orders_failed: int
    deal_count: int
    buy_deals: int
    sell_deals: int
    deal_volume: float
    snapshot_count: int

    def to_dict(self) -> dict:
        return {
            "period": self.period,
            "label": self.label,
            "strategy_name": self.strategy_name,
            "start_assets": self.start_assets,
            "end_assets": self.end_assets,
            "return_pct": self.return_pct,
            "cash_end": self.cash_end,
            "market_val_end": self.market_val_end,
            "signal_count": self.signal_count,
            "rejected_count": self.rejected_count,
            "orders_submitted": self.orders_submitted,
            "orders_failed": self.orders_failed,
            "deal_count": self.deal_count,
            "buy_deals": self.buy_deals,
            "sell_deals": self.sell_deals,
            "deal_volume": self.deal_volume,
            "snapshot_count": self.snapshot_count,
        }


class PerformanceReporter:
    def __init__(self, store: JournalStore) -> None:
        self._store = store

    def build(
        self,
        period: Period,
        *,
        strategy_name: str | None = None,
        anchor: datetime | None = None,
    ) -> PerformanceReport:
        start_ts, end_ts = self._store.local_date_bounds(period, anchor=anchor)
        label = self._format_label(period, start_ts)

        snapshots = self._store.fetch_snapshots(
            start_ts=start_ts,
            end_ts=end_ts,
            strategy_name=strategy_name,
        )
        if not snapshots:
            snapshots = self._store.fetch_snapshots(strategy_name=strategy_name)

        start_assets = snapshots[0]["total_assets"] if snapshots else None
        end_row = snapshots[-1] if snapshots else None
        end_assets = end_row["total_assets"] if end_row else None
        cash_end = end_row["cash"] if end_row else None
        market_val_end = end_row["market_val"] if end_row else None

        return_pct = None
        if start_assets and end_assets and start_assets > 0:
            return_pct = (end_assets - start_assets) / start_assets * 100.0

        deals = self._store.fetch_deals(
            start_ts=start_ts,
            end_ts=end_ts,
            strategy_name=strategy_name,
        )
        buy_deals = sum(1 for d in deals if d["side"] == "BUY")
        sell_deals = sum(1 for d in deals if d["side"] == "SELL")
        deal_volume = sum(float(d["qty"]) * float(d["price"]) for d in deals)

        return PerformanceReport(
            period=period,
            label=label,
            strategy_name=strategy_name,
            start_assets=start_assets,
            end_assets=end_assets,
            return_pct=return_pct,
            cash_end=cash_end,
            market_val_end=market_val_end,
            signal_count=self._store.count_events(
                "signal", strategy_name=strategy_name, start_ts=start_ts, end_ts=end_ts
            ),
            rejected_count=self._store.count_events(
                "risk_rejected", strategy_name=strategy_name, start_ts=start_ts, end_ts=end_ts
            ),
            orders_submitted=self._store.count_events(
                "order_submitted", strategy_name=strategy_name, start_ts=start_ts, end_ts=end_ts
            ),
            orders_failed=self._store.count_events(
                "order_failed", strategy_name=strategy_name, start_ts=start_ts, end_ts=end_ts
            ),
            deal_count=len(deals),
            buy_deals=buy_deals,
            sell_deals=sell_deals,
            deal_volume=deal_volume,
            snapshot_count=len(snapshots),
        )

    def _format_label(self, period: Period, start_ts: str) -> str:
        tz = ZoneInfo("Asia/Hong_Kong")
        start = datetime.fromisoformat(start_ts).astimezone(tz)
        if period == "day":
            return start.strftime("%Y-%m-%d")
        if period == "week":
            iso = start.isocalendar()
            return f"{iso.year}-W{iso.week:02d}"
        return start.strftime("%Y-%m")


def format_report_text(report: PerformanceReport) -> str:
    lines = [
        f"Performance Report — {report.label} ({report.period})",
        "─" * 48,
    ]
    if report.strategy_name:
        lines.append(f"Strategy      : {report.strategy_name}")
    if report.start_assets is not None and report.end_assets is not None:
        lines.append(
            f"Assets        : {report.start_assets:,.2f} → {report.end_assets:,.2f}"
        )
    if report.return_pct is not None:
        lines.append(f"Return        : {report.return_pct:+.2f}%")
    if report.cash_end is not None:
        lines.append(f"Cash (end)    : {report.cash_end:,.2f}")
    if report.market_val_end is not None:
        lines.append(f"Market val    : {report.market_val_end:,.2f}")
    lines.extend(
        [
            f"Signals       : {report.signal_count}",
            f"Rejected      : {report.rejected_count}",
            f"Orders sent   : {report.orders_submitted}",
            f"Orders failed : {report.orders_failed}",
            f"Deals (fills) : {report.deal_count}  (BUY {report.buy_deals} / SELL {report.sell_deals})",
            f"Deal volume   : {report.deal_volume:,.2f}",
            f"Snapshots     : {report.snapshot_count}",
        ]
    )
    return "\n".join(lines)
