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


def base_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--strategy", required=True, help="Strategy name (registry key)")
    parser.add_argument("--market", default="HK", choices=["HK", "US"], help="Trading market")
    parser.add_argument(
        "--env",
        default="simulate",
        choices=["simulate", "real"],
        help="Trading environment (default: simulate)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser


def apply_env_override(settings: dict, env: str) -> dict:
    settings = dict(settings)
    trading = dict(settings.get("trading", {}))
    trading["env"] = env
    settings["trading"] = trading
    return settings


def confirm_real_trading() -> bool:
    print("\n⚠️  REAL TRADING MODE — actual orders will be placed.")
    answer = input("Type 'YES' to confirm: ")
    return answer.strip() == "YES"
