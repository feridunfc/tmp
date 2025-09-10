from __future__ import annotations
import pandas as pd
from typing import Protocol, Dict

class StrategyBase(Protocol):
    name: str
    params: Dict
    def prepare(self, df: pd.DataFrame)->pd.DataFrame: ...
    def generate_signals(self, df: pd.DataFrame)->pd.Series: ...  # -1/0/+1

STRATEGY_REGISTRY: dict[str, type] = {}

def register_strategy(cls):
    STRATEGY_REGISTRY[getattr(cls, "name", cls.__name__)] = cls
    return cls
