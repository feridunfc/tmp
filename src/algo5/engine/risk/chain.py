from __future__ import annotations
import pandas as pd
from .rules import Rule
from .sizer import Sizer


class RiskChain:
    def __init__(self, sizer: Sizer, rules: list[Rule] | None = None):
        self.sizer = sizer
        self.rules = list(rules or [])

    def add(self, rule: Rule) -> None:
        self.rules.append(rule)

    def run(self, returns: pd.Series, signal: pd.Series) -> pd.Series:
        w = self.sizer.size(returns, signal)
        for r in self.rules:
            w = r.apply(returns, w)
        return w.clip(0.0, 1.0)
