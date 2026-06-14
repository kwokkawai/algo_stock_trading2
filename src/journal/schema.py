"""SQLite schema for the trade journal."""

SCHEMA_VERSION = 1

DDL = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS run_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT UNIQUE NOT NULL,
    strategy_name TEXT NOT NULL,
    market TEXT NOT NULL,
    mode TEXT NOT NULL,
    env TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    event_type TEXT NOT NULL,
    strategy_name TEXT,
    run_id TEXT,
    symbol TEXT,
    side TEXT,
    qty INTEGER,
    price REAL,
    reason TEXT,
    order_id TEXT,
    payload_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_strategy ON events(strategy_name);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT UNIQUE NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    qty INTEGER NOT NULL,
    price REAL,
    order_status TEXT,
    dealt_qty INTEGER,
    dealt_avg_price REAL,
    create_time TEXT,
    updated_time TEXT,
    env TEXT NOT NULL,
    strategy_name TEXT,
    reason TEXT,
    synced_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);
CREATE INDEX IF NOT EXISTS idx_orders_create ON orders(create_time);

CREATE TABLE IF NOT EXISTS deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id TEXT UNIQUE NOT NULL,
    order_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    qty INTEGER NOT NULL,
    price REAL NOT NULL,
    create_time TEXT,
    env TEXT NOT NULL,
    synced_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_deals_create ON deals(create_time);
CREATE INDEX IF NOT EXISTS idx_deals_symbol ON deals(symbol);

CREATE TABLE IF NOT EXISTS account_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    snapshot_type TEXT NOT NULL,
    env TEXT NOT NULL,
    strategy_name TEXT,
    run_id TEXT,
    total_assets REAL NOT NULL,
    cash REAL NOT NULL,
    market_val REAL NOT NULL,
    positions_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_snapshots_ts ON account_snapshots(ts);
CREATE INDEX IF NOT EXISTS idx_snapshots_type ON account_snapshots(snapshot_type);
"""
