from src.data.subscription import DataSubscription, merge_subscriptions


def test_merge_subscriptions():
    a = DataSubscription(symbols=["HK.00700"], intervals=["1d"])
    b = DataSubscription(symbols=["HK.09988", "HK.00700"], intervals=["1m"], tick=True)
    merged = merge_subscriptions([a, b])
    assert merged.symbols == ["HK.00700", "HK.09988"]
    assert set(merged.intervals) == {"1d", "1m"}
    assert merged.tick is True
