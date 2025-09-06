# strategies/rule_based/atr_breakout.py
from __future__ import annotations

import numpy as np
import pandas as pd
from strategies.registry import Field

NAME = "ATR Breakout"

# UI/registry'nin okuyabileceği statik şema (dict)
SCHEMA = {
    "atr_window":   {"type": "int",   "default": 14,  "low": 5,  "high": 100},
    "k":            {"type": "float", "default": 1.0, "low": 0.5, "high": 5.0, "step": 0.1},
    "use_prev_close": {"type": "bool","default": True},
    "direction":    {"type": "str",   "default": "both", "options": ["long", "short", "both"]},
}


class ATRBreakout:
    """
    Standart arayüz:
      - param_schema() -> List[Field]
      - prepare(df, **params) -> DataFrame
      - generate_signals(df, **params) -> Series in {-1,0,1}
    """
    family = "rule_based"
    name = NAME
    values = [-1, 0, 1]  # UI bilgi amaçlı

    @staticmethod
    def _get(series_map: dict[str, pd.Series], *candidates: str) -> pd.Series:
        for c in candidates:
            if c in series_map:
                return series_map[c]
        raise KeyError(f"Missing column(s): tried {candidates}")

    @staticmethod
    def param_schema():
        # UI formu için Field listesi
        return [
            Field(name="atr_window", type="int",   default=SCHEMA["atr_window"]["default"], low=5,  high=100),
            Field(name="k",          type="float", default=SCHEMA["k"]["default"],         low=0.5, high=5.0, step=0.1),
            Field(name="use_prev_close", type="bool", default=SCHEMA["use_prev_close"]["default"]),
            Field(name="direction",  type="select", default=SCHEMA["direction"]["default"], options=SCHEMA["direction"]["options"]),
        ]

    @staticmethod
    def prepare(df: pd.DataFrame, **params) -> pd.DataFrame:
        """
        ATR, üst/alt bantların hesaplanması.
        """
        n = int(params.get("atr_window", SCHEMA["atr_window"]["default"]))
        k = float(params.get("k", SCHEMA["k"]["default"]))
        use_prev = bool(params.get("use_prev_close", SCHEMA["use_prev_close"]["default"]))

        cols = {c: df[c] for c in df.columns}
        o = ATRBreakout._get(cols, "Open", "open")
        h = ATRBreakout._get(cols, "High", "high")
        l = ATRBreakout._get(cols, "Low", "low")
        c = ATRBreakout._get(cols, "Close", "close")

        out = df.copy()
        prev_close = c.shift(1) if use_prev else c
        tr = pd.concat([(h - l).abs(), (h - prev_close).abs(), (l - prev_close).abs()], axis=1).max(axis=1)
        out["atr"] = tr.rolling(n, min_periods=n).mean()

        # bantlar
        out["upper"] = prev_close + k * out["atr"]
        out["lower"] = prev_close - k * out["atr"]
        return out

    @staticmethod
    def generate_signals(df: pd.DataFrame, **params) -> pd.Series:
        """
        Kırılım olduğunda 1/-1; aksi halde 0.
        direction: long/short/both
        """
        direction = (params.get("direction", SCHEMA["direction"]["default"]) or "both").lower()
        c = df["Close"] if "Close" in df.columns else df["close"]
        up = df["upper"]; lo = df["lower"]

        long_sig = (c > up).astype(int)
        short_sig = -(c < lo).astype(int)

        if direction == "long":
            raw = long_sig
        elif direction == "short":
            raw = short_sig
        else:  # both
            raw = long_sig + short_sig  # aynı bar’da çakışma pek mümkün değil; olursa 0’a indir
            raw = raw.clip(lower=-1, upper=1)

        return pd.Series(raw.values, index=df.index, name="signal")


# Eski adapterler / registry wrapper’ları için modül düzeyinde fonksiyonlar:
def param_schema():        return ATRBreakout.param_schema()
def prepare(df, **params): return ATRBreakout.prepare(df, **params)
def generate_signals(df, **params): return ATRBreakout.generate_signals(df, **params)
