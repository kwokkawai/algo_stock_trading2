import pytest

from src.trading_policy import (
    PaperOnlyError,
    apply_paper_only_settings,
    assert_paper_trade_allowed,
    is_paper_only,
    resolve_trading_env,
)


def _settings(paper_only: bool = True, env: str = "simulate") -> dict:
    return {"trading": {"paper_only": paper_only, "env": env}}


def test_paper_only_defaults_true():
    assert is_paper_only({}) is True
    assert is_paper_only({"trading": {}}) is True


def test_forces_simulate_when_paper_only():
    assert resolve_trading_env(_settings(), "simulate") == "simulate"
    assert resolve_trading_env(_settings(), None) == "simulate"


def test_rejects_real_when_paper_only():
    with pytest.raises(PaperOnlyError):
        resolve_trading_env(_settings(paper_only=True), "real")


def test_allows_real_when_unlocked():
    assert resolve_trading_env(_settings(paper_only=False), "real") == "real"


def test_apply_paper_only_overrides_real_env():
    settings = apply_paper_only_settings(_settings(env="real"))
    assert settings["trading"]["env"] == "simulate"


def test_assert_paper_trade_allowed_blocks_live():
    with pytest.raises(PaperOnlyError):
        assert_paper_trade_allowed(_settings())
