"""Configuration loading utilities."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"


def load_settings(path: Path | None = None) -> dict:
    settings_path = path or CONFIG_DIR / "settings.yaml"
    if not settings_path.exists():
        settings_path = CONFIG_DIR / "settings.example.yaml"
    with open(settings_path) as f:
        return yaml.safe_load(f)


def load_strategy_config(name: str) -> dict:
    strategy_path = CONFIG_DIR / "strategies" / f"{name}.yaml"
    if not strategy_path.exists():
        raise FileNotFoundError(f"Strategy config not found: {strategy_path}")
    with open(strategy_path) as f:
        config = yaml.safe_load(f)
    params = config.get("params", {})
    params.setdefault("symbols", config.get("symbols", []))
    params.setdefault("market", config.get("market", "HK"))
    return config
