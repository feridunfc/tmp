from __future__ import annotations
from dataclasses import dataclass
import pandas as pd


class Rule:
    def apply(self, returns: pd.Series, weights: pd.Series):  # pure function
        raise NotImplementedError


@dataclass
class VolTargetRule(Rule):
    target_pct: float = 15.0
    lookback: int = 20
    ann: int = 252

    def apply(self, returns: pd.Series, weights: pd.Series):
        rets = returns.astype(float).fillna(0.0)
        vol = rets.ewm(span=int(max(2, self.lookback)), adjust=False).std(bias=False)
        ann_vol = vol * (float(self.ann) ** 0.5)
        scale = (float(self.target_pct) / 100.0) / ann_vol.replace(0.0, float("nan"))
        scale = scale.clip(upper=1.0).fillna(1.0)
        return (weights.astype(float) * scale).clip(0.0, 1.0)
