from dataclasses import dataclass, field


@dataclass
class DataSubscription:
    symbols: list[str] = field(default_factory=list)
    intervals: list[str] = field(default_factory=list)
    tick: bool = False

    def merge(self, other: "DataSubscription") -> "DataSubscription":
        return DataSubscription(
            symbols=sorted(set(self.symbols + other.symbols)),
            intervals=sorted(set(self.intervals + other.intervals)),
            tick=self.tick or other.tick,
        )


INTERVAL_TO_SUBTYPE = {
    "1d": "K_DAY",
    "1m": "K_1M",
}


def merge_subscriptions(subscriptions: list[DataSubscription]) -> DataSubscription:
    merged = DataSubscription()
    for sub in subscriptions:
        merged = merged.merge(sub)
    return merged
