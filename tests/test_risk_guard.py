from src.models.signal import Signal, SignalSide
from src.risk.guard import RiskConfig, RiskGuard


def _guard(**overrides) -> RiskGuard:
    cfg = RiskConfig(
        max_notional_per_order=50000,
        allowed_symbols={"HK": ["HK.00700"]},
        signal_cooldown_seconds=0,
    )
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return RiskGuard(cfg)


def test_whitelist_rejects_unknown_symbol():
    guard = _guard()
    signals = [
        Signal(symbol="HK.99999", side=SignalSide.BUY, qty=100, price=10.0, reason="test")
    ]
    result = guard.validate(signals)
    assert result.approved == []
    assert len(result.rejected) == 1


def test_approves_whitelisted_symbol():
    guard = _guard()
    signals = [
        Signal(symbol="HK.00700", side=SignalSide.BUY, qty=100, price=10.0, reason="test")
    ]
    result = guard.validate(signals, account_total=1_000_000)
    assert len(result.approved) == 1
    assert result.approved[0].symbol == "HK.00700"


def test_rejects_sell_without_position():
    guard = _guard()
    signals = [
        Signal(symbol="HK.00700", side=SignalSide.SELL, qty=100, price=10.0, reason="test")
    ]
    result = guard.validate(signals, positions=[])
    assert result.approved == []


def test_notional_limit():
    guard = _guard(max_notional_per_order=1000)
    signals = [
        Signal(symbol="HK.00700", side=SignalSide.BUY, qty=100, price=100.0, reason="test")
    ]
    result = guard.validate(signals)
    assert result.approved == []
