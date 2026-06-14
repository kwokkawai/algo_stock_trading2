"""Shared indicator helpers for strategy implementations."""

from __future__ import annotations

import math


def ema_series(closes: list[float], period: int) -> list[float | None]:
    """Return EMA values aligned with closes (None until period samples exist)."""
    if period <= 0 or not closes:
        return []
    k = 2.0 / (period + 1)
    result: list[float | None] = []
    ema_val: float | None = None
    for i, price in enumerate(closes):
        if ema_val is None:
            if i + 1 < period:
                result.append(None)
                continue
            ema_val = sum(closes[i + 1 - period : i + 1]) / period
        else:
            ema_val = price * k + ema_val * (1 - k)
        result.append(ema_val)
    return result


def rsi(closes: list[float], period: int) -> float | None:
    if len(closes) < period + 1:
        return None
    gains = 0.0
    losses = 0.0
    segment = closes[-(period + 1) :]
    for i in range(1, len(segment)):
        delta = segment[i] - segment[i - 1]
        if delta >= 0:
            gains += delta
        else:
            losses -= delta
    if losses == 0:
        return 100.0
    rs = gains / losses
    return 100.0 - (100.0 / (1.0 + rs))


def bollinger_bands(
    closes: list[float], period: int, num_std: float
) -> tuple[float, float, float] | None:
    if len(closes) < period:
        return None
    window = closes[-period:]
    middle = sum(window) / period
    variance = sum((x - middle) ** 2 for x in window) / period
    std = math.sqrt(variance)
    return middle - num_std * std, middle, middle + num_std * std
