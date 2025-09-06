from dataclasses import dataclass


@dataclass(frozen=True)
class OhlcvSchema:
    required: tuple[str, ...] = ("Open", "High", "Low", "Close", "Volume")
    allow_extras: bool = True
