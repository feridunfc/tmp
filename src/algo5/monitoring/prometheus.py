from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict
@dataclass
class Counter:
    name: str; help: str = ""; _value: float = 0.0
    def inc(self, amount: float = 1.0) -> None: self._value += amount
    @property
    def value(self) -> float: return self._value
@dataclass
class Gauge:
    name: str; help: str = ""; _value: float = 0.0
    def set(self, value: float) -> None: self._value = float(value)
    @property
    def value(self) -> float: return self._value
@dataclass
class MetricsRegistry:
    counters: Dict[str, Counter] = field(default_factory=dict)
    gauges: Dict[str, Gauge] = field(default_factory=dict)
    def counter(self, name: str, help: str = "") -> Counter:
        if name not in self.counters: self.counters[name] = Counter(name, help); return self.counters[name]
        return self.counters[name]
    def gauge(self, name: str, help: str = "") -> Gauge:
        if name not in self.gauges: self.gauges[name] = Gauge(name, help); return self.gauges[name]
        return self.gauges[name]
REGISTRY = MetricsRegistry()
