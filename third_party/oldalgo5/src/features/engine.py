from __future__ import annotations
import pandas as pd, numpy as np
from typing import Callable, Dict

FeatureFn = Callable[[pd.DataFrame, dict], pd.DataFrame]

class FeatureEngine:
    def __init__(self):
        self.registry: Dict[str, FeatureFn] = {}
        self.register("sma", self._sma)
        self.register("rsi", self._rsi)
        self.register("rv",  self._rv)
        self.register("z_anomaly", self._z_anomaly)

    def register(self, name: str, fn: FeatureFn):
        self.registry[name] = fn

    def build(self, df: pd.DataFrame, features: list[tuple[str,dict]])->pd.DataFrame:
        out = df.copy()
        for name, params in features:
            if name not in self.registry:
                raise ValueError(f"Unknown feature: {name}")
            out = self.registry[name](out, params or {})
        return out

    # ---- builtins ----
    def _sma(self, df, p):
        for w in p.get("windows", [10, 20, 50]):
            df[f"sma_{w}"] = df["close"].rolling(w).mean()
        return df

    def _rsi(self, df, p):
        n = p.get("window", 14)
        d = df["close"].diff()
        up = d.clip(lower=0).rolling(n).mean()
        dn = (-d.clip(upper=0)).rolling(n).mean()
        rs = up / (dn + 1e-12)
        df["rsi"] = 100 - 100 / (1 + rs)
        return df

    def _rv(self, df, p):
        n = p.get("window", 20)
        r = df["close"].pct_change()
        df[f"rv_{n}"] = r.rolling(n).std(ddof=0) * np.sqrt(252)
        return df

    def _z_anomaly(self, df, p):
        n = p.get("window", 50); zt = p.get("z", 3.0)
        r = df["close"].pct_change()
        mu = r.rolling(n).mean(); sd = r.rolling(n).std(ddof=0)
        df["ret_z"] = (r - mu) / (sd + 1e-12)
        df["anomaly_flag"] = (df["ret_z"].abs() > zt).astype(int)
        return df
