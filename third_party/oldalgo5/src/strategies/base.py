from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from typing import Dict, Any, List
import pandas as pd

class Strategy:
    # Lightweight base: normalize columns + interface stubs.
    family = "rule"
    name = "BaseStrategy"

    def __init__(self, **params):
        self.params = params or {}

    # --- helpers ---
    @staticmethod
    def _normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
        cols = {c.lower(): c for c in df.columns}
        def pick(*opts):
            for o in opts:
                if o in cols:
                    return cols[o]
            return None
        mapping = {
            "Open":  pick("open","o"),
            "High":  pick("high","h"),
            "Low":   pick("low","l"),
            "Close": pick("close","c","adj_close","adjclose"),
            "Volume":pick("volume","vol","v"),
        }
        out = {}
        for k, src in mapping.items():
            if src and src in df.columns:
                out[k] = df[src]
        out_df = pd.DataFrame(out, index=df.index)
        return out_df

    # --- interface ---
    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._normalize_ohlcv(df)

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:  # type: ignore[name-defined]
        raise NotImplementedError

    # optional schema support via dataclass ParamSchema on subclasses
    @classmethod
    def param_schema(cls) -> List[Dict[str, Any]]:
        ps = getattr(cls, "ParamSchema", None)
        if ps and is_dataclass(ps):
            sch = []
            for f in fields(ps):
                meta = dict(f.metadata) if f.metadata else {}
                sch.append({
                    "name": f.name,
                    "type": f.type.__name__ if hasattr(f.type, "__name__") else str(f.type),
                    "default": f.default,
                    **meta
                })
            return sch
        return []
