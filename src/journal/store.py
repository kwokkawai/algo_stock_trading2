"""SQLite journal store — append-only event and snapshot persistence."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator
from zoneinfo import ZoneInfo

from src.journal.paths import default_db_path
from src.journal.schema import DDL, SCHEMA_VERSION
from src.models.order import AccountInfo, DealRecord, OrderRecord, Position
from src.models.signal import Signal


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class JournalStore:
    def __init__(self, db_path: Path | str, timezone_name: str = "Asia/Hong_Kong") -> None:
        self._db_path = Path(db_path)
        self._tz = ZoneInfo(timezone_name)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @classmethod
    def from_settings(cls, settings: dict) -> "JournalStore":
        journal_cfg = settings.get("journal", {})
        if not journal_cfg.get("enabled", True):
            raise RuntimeError("Journal is disabled in settings")
        return cls(
            db_path=default_db_path(settings),
            timezone_name=journal_cfg.get("timezone", "Asia/Hong_Kong"),
        )

    @property
    def db_path(self) -> Path:
        return self._db_path

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(DDL)
            conn.execute(
                "INSERT OR IGNORE INTO schema_meta (key, value) VALUES (?, ?)",
                ("version", str(SCHEMA_VERSION)),
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def new_run_id(self) -> str:
        return str(uuid.uuid4())

    def start_session(
        self,
        run_id: str,
        strategy_name: str,
        market: str,
        mode: str,
        env: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO run_sessions (run_id, strategy_name, market, mode, env, started_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (run_id, strategy_name, market, mode, env, _utc_now_iso()),
            )

    def end_session(self, run_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE run_sessions SET ended_at = ? WHERE run_id = ?",
                (_utc_now_iso(), run_id),
            )

    def record_signal(
        self,
        signal: Signal,
        *,
        strategy_name: str,
        run_id: str | None = None,
    ) -> None:
        self._insert_event(
            event_type="signal",
            strategy_name=strategy_name,
            run_id=run_id,
            symbol=signal.symbol,
            side=signal.side.value,
            qty=signal.qty,
            price=signal.price,
            reason=signal.reason,
        )

    def record_risk_rejected(
        self,
        signal: Signal,
        reject_reason: str,
        *,
        strategy_name: str,
        run_id: str | None = None,
    ) -> None:
        self._insert_event(
            event_type="risk_rejected",
            strategy_name=strategy_name,
            run_id=run_id,
            symbol=signal.symbol,
            side=signal.side.value,
            qty=signal.qty,
            price=signal.price,
            reason=f"{reject_reason} | {signal.reason}".strip(" |"),
        )

    def record_order_submitted(
        self,
        *,
        order_id: str,
        symbol: str,
        side: str,
        qty: int,
        price: float | None,
        reason: str,
        env: str,
        strategy_name: str,
        run_id: str | None = None,
    ) -> None:
        ts = _utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO events (
                    ts, event_type, strategy_name, run_id, symbol, side, qty, price, reason, order_id
                ) VALUES (?, 'order_submitted', ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (ts, strategy_name, run_id, symbol, side, qty, price, reason, order_id),
            )
            conn.execute(
                """
                INSERT INTO orders (
                    order_id, symbol, side, qty, price, order_status, dealt_qty, dealt_avg_price,
                    create_time, updated_time, env, strategy_name, reason, synced_at
                ) VALUES (?, ?, ?, ?, ?, 'SUBMITTED', 0, NULL, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(order_id) DO UPDATE SET
                    order_status = excluded.order_status,
                    price = excluded.price,
                    reason = COALESCE(orders.reason, excluded.reason),
                    strategy_name = COALESCE(orders.strategy_name, excluded.strategy_name),
                    synced_at = excluded.synced_at
                """,
                (
                    order_id,
                    symbol,
                    side,
                    qty,
                    price,
                    ts,
                    ts,
                    env,
                    strategy_name,
                    reason,
                    ts,
                ),
            )

    def record_order_failed(
        self,
        *,
        symbol: str,
        side: str,
        qty: int,
        price: float | None,
        reason: str,
        message: str,
        strategy_name: str,
        run_id: str | None = None,
    ) -> None:
        self._insert_event(
            event_type="order_failed",
            strategy_name=strategy_name,
            run_id=run_id,
            symbol=symbol,
            side=side,
            qty=qty,
            price=price,
            reason=f"{reason} | {message}".strip(" |"),
        )

    def upsert_orders(self, orders: list[OrderRecord]) -> int:
        if not orders:
            return 0
        ts = _utc_now_iso()
        with self._connect() as conn:
            for order in orders:
                conn.execute(
                    """
                    INSERT INTO orders (
                        order_id, symbol, side, qty, price, order_status, dealt_qty, dealt_avg_price,
                        create_time, updated_time, env, strategy_name, reason, synced_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(order_id) DO UPDATE SET
                        order_status = excluded.order_status,
                        dealt_qty = excluded.dealt_qty,
                        dealt_avg_price = excluded.dealt_avg_price,
                        updated_time = excluded.updated_time,
                        synced_at = excluded.synced_at
                    """,
                    (
                        order.order_id,
                        order.symbol,
                        order.side.value if hasattr(order.side, "value") else str(order.side),
                        order.qty,
                        order.price,
                        order.order_status,
                        order.dealt_qty,
                        order.dealt_avg_price,
                        order.create_time,
                        order.updated_time,
                        order.env,
                        order.strategy_name,
                        order.reason,
                        ts,
                    ),
                )
        return len(orders)

    def upsert_deals(self, deals: list[DealRecord]) -> int:
        if not deals:
            return 0
        ts = _utc_now_iso()
        with self._connect() as conn:
            for deal in deals:
                conn.execute(
                    """
                    INSERT INTO deals (
                        deal_id, order_id, symbol, side, qty, price, create_time, env, synced_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(deal_id) DO UPDATE SET
                        qty = excluded.qty,
                        price = excluded.price,
                        create_time = excluded.create_time,
                        synced_at = excluded.synced_at
                    """,
                    (
                        deal.deal_id,
                        deal.order_id,
                        deal.symbol,
                        deal.side.value if hasattr(deal.side, "value") else str(deal.side),
                        deal.qty,
                        deal.price,
                        deal.create_time,
                        deal.env,
                        ts,
                    ),
                )
        return len(deals)

    def record_snapshot(
        self,
        account: AccountInfo,
        positions: list[Position],
        *,
        snapshot_type: str,
        strategy_name: str | None = None,
        run_id: str | None = None,
    ) -> None:
        positions_payload = [
            {
                "symbol": p.symbol,
                "qty": p.qty,
                "cost_price": p.cost_price,
                "market_value": p.market_value,
            }
            for p in positions
        ]
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO account_snapshots (
                    ts, snapshot_type, env, strategy_name, run_id,
                    total_assets, cash, market_val, positions_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _utc_now_iso(),
                    snapshot_type,
                    account.env,
                    strategy_name,
                    run_id,
                    account.total_assets,
                    account.cash,
                    account.market_val,
                    json.dumps(positions_payload),
                ),
            )

    def _insert_event(
        self,
        *,
        event_type: str,
        strategy_name: str | None = None,
        run_id: str | None = None,
        symbol: str | None = None,
        side: str | None = None,
        qty: int | None = None,
        price: float | None = None,
        reason: str | None = None,
        order_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO events (
                    ts, event_type, strategy_name, run_id, symbol, side, qty, price, reason, order_id, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _utc_now_iso(),
                    event_type,
                    strategy_name,
                    run_id,
                    symbol,
                    side,
                    qty,
                    price,
                    reason,
                    order_id,
                    json.dumps(payload) if payload else None,
                ),
            )

    def count_events(
        self,
        event_type: str,
        *,
        strategy_name: str | None = None,
        start_ts: str | None = None,
        end_ts: str | None = None,
    ) -> int:
        query = "SELECT COUNT(*) AS n FROM events WHERE event_type = ?"
        params: list[Any] = [event_type]
        if strategy_name:
            query += " AND strategy_name = ?"
            params.append(strategy_name)
        if start_ts:
            query += " AND ts >= ?"
            params.append(start_ts)
        if end_ts:
            query += " AND ts < ?"
            params.append(end_ts)
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
            return int(row["n"]) if row else 0

    def fetch_snapshots(
        self,
        *,
        start_ts: str | None = None,
        end_ts: str | None = None,
        snapshot_type: str | None = None,
        strategy_name: str | None = None,
    ) -> list[sqlite3.Row]:
        query = "SELECT * FROM account_snapshots WHERE 1=1"
        params: list[Any] = []
        if start_ts:
            query += " AND ts >= ?"
            params.append(start_ts)
        if end_ts:
            query += " AND ts < ?"
            params.append(end_ts)
        if snapshot_type:
            query += " AND snapshot_type = ?"
            params.append(snapshot_type)
        if strategy_name:
            query += " AND strategy_name = ?"
            params.append(strategy_name)
        query += " ORDER BY ts ASC"
        with self._connect() as conn:
            return list(conn.execute(query, params).fetchall())

    def fetch_deals(
        self,
        *,
        start_ts: str | None = None,
        end_ts: str | None = None,
        strategy_name: str | None = None,
    ) -> list[sqlite3.Row]:
        query = """
            SELECT d.*, o.strategy_name
            FROM deals d
            LEFT JOIN orders o ON o.order_id = d.order_id
            WHERE 1=1
        """
        params: list[Any] = []
        if start_ts:
            query += " AND COALESCE(d.create_time, d.synced_at) >= ?"
            params.append(start_ts)
        if end_ts:
            query += " AND COALESCE(d.create_time, d.synced_at) < ?"
            params.append(end_ts)
        if strategy_name:
            query += " AND o.strategy_name = ?"
            params.append(strategy_name)
        query += " ORDER BY COALESCE(d.create_time, d.synced_at) ASC"
        with self._connect() as conn:
            return list(conn.execute(query, params).fetchall())

    def local_date_bounds(self, period: str, anchor: datetime | None = None) -> tuple[str, str]:
        """Return UTC ISO bounds [start, end) for day/week/month in journal timezone."""
        now = anchor or datetime.now(self._tz)
        if period == "day":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period == "week":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start = start - timedelta(days=start.weekday())
            end = start + timedelta(days=7)
        elif period == "month":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
        else:
            raise ValueError(f"Unknown period: {period}")

        return (
            start.astimezone(timezone.utc).replace(microsecond=0).isoformat(),
            end.astimezone(timezone.utc).replace(microsecond=0).isoformat(),
        )
