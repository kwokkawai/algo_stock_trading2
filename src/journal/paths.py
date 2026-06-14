"""Journal file paths."""

from __future__ import annotations

from pathlib import Path

from src.config import ROOT


def default_db_path(settings: dict | None = None) -> Path:
    journal_cfg = (settings or {}).get("journal", {})
    rel = journal_cfg.get("db_path", "data/journal/trades.db")
    path = Path(rel)
    if not path.is_absolute():
        path = ROOT / path
    return path
