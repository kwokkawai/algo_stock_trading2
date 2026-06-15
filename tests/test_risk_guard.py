from src.models.order import Position
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
    assert result.rejected[0][1].startswith("insufficient position")


def test_notional_limit():
    guard = _guard(max_notional_per_order=1000)
    signals = [
        Signal(symbol="HK.00700", side=SignalSide.BUY, qty=100, price=100.0, reason="test")
    ]
    result = guard.validate(signals)
    assert result.approved == []
    assert "notional" in result.rejected[0][1]


def test_cooldown_rejects_rapid_repeat():
    guard = _guard(signal_cooldown_seconds=60)
    signal = Signal(symbol="HK.00700", side=SignalSide.BUY, qty=100, price=10.0, reason="test")
    first = guard.validate([signal], account_total=1_000_000)
    assert len(first.approved) == 1
    second = guard.validate([signal], account_total=1_000_000)
    assert second.approved == []
    assert "cooldown" in second.rejected[0][1]


def test_position_pct_limit():
    guard = _guard(max_position_pct=0.1, max_notional_per_order=500_000)
    signals = [
        Signal(symbol="HK.00700", side=SignalSide.BUY, qty=100, price=200.0, reason="test")
    ]
    # 100 * 200 = 20k; account 100k → 20% > 10%
    result = guard.validate(signals, account_total=100_000, positions=[])
    assert result.approved == []
    assert "position would exceed" in result.rejected[0][1]


def test_position_pct_allows_within_limit():
    guard = _guard(max_position_pct=0.25, max_notional_per_order=500_000)
    signals = [
        Signal(symbol="HK.00700", side=SignalSide.BUY, qty=100, price=200.0, reason="test")
    ]
    result = guard.validate(signals, account_total=1_000_000, positions=[])
    assert len(result.approved) == 1


def test_daily_loss_halt_blocks_all():
    guard = _guard(daily_loss_limit=10_000)
    guard._daily_pnl = -10_001
    signals = [
        Signal(symbol="HK.00700", side=SignalSide.BUY, qty=100, price=10.0, reason="test")
    ]
    result = guard.validate(signals, account_total=1_000_000)
    assert result.approved == []
    assert guard.is_halted()


def test_sell_with_position_ok():
    guard = _guard()
    positions = [Position(symbol="HK.00700", qty=200, cost_price=400, market_value=80000)]
    signals = [
        Signal(symbol="HK.00700", side=SignalSide.SELL, qty=100, price=400.0, reason="test")
    ]
    result = guard.validate(signals, positions=positions, account_total=1_000_000)
    assert len(result.approved) == 1
