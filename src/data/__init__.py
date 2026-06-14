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
