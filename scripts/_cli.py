#!/usr/bin/env python3
"""Shared CLI utilities."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def paper_parser(description: str) -> argparse.ArgumentParser:
    """Parser for paper/simulate trading scripts — no --env real option."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--strategy", required=True, help="Strategy name (registry key)")
    parser.add_argument("--market", default="HK", choices=["HK", "US"], help="Trading market")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser


def base_parser(description: str) -> argparse.ArgumentParser:
    """Legacy parser — prefer paper_parser for simulate-only scripts."""
    return paper_parser(description)


def status_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--market", default="HK", choices=["HK", "US"], help="Trading market")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser


def load_trading_settings() -> dict:
    """Load settings with paper_only policy applied (always simulate when locked)."""
    from src.config import load_settings

    return load_settings()


def apply_env_override(settings: dict, env: str) -> dict:
    from src.trading_policy import PaperOnlyError, resolve_trading_env

    settings = dict(settings)
    trading = dict(settings.get("trading", {}))
    try:
        trading["env"] = resolve_trading_env(settings, env)
    except PaperOnlyError:
        raise
    settings["trading"] = trading
    return settings


def confirm_real_trading() -> bool:
    print("\n⚠️  REAL TRADING MODE — actual orders will be placed.")
    answer = input("Type 'YES' to confirm: ")
    return answer.strip() == "YES"
