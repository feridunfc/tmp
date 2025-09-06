from __future__ import annotations
import pandas as pd
from dataclasses import dataclass
from typing import Dict

@dataclass
class ValidationReport:
    is_valid: bool
    issues: Dict[str, dict]

class DataValidator:
    def __init__(self, strict: bool = True, max_gap_ratio: float = 0.02):
        self.strict = strict
        self.max_gap_ratio = max_gap_ratio

    def validate_ohlcv(self, df: pd.DataFrame, symbol: str) -> ValidationReport:
        issues: Dict[str, dict] = {}
        req = ["open","high","low","close","volume"]
        missing = [c for c in req if c not in df.columns]
        if missing:
            issues["missing_columns"] = {"missing": missing}

        # NaN ratios
        nan_ratio = df.reindex(columns=req).isna().mean(numeric_only=True).to_dict()
        for k, v in nan_ratio.items():
            if v and v > 0:
                issues[f"nan_{k}"] = {"ratio": float(v)}

        # Price consistency
        if all(c in df.columns for c in ["open","high","low","close"]):
            bad = ~((df["low"] <= df["open"]) & (df["open"] <= df["high"]) &
                    (df["low"] <= df["close"]) & (df["close"] <= df["high"]))
            if bad.any():
                issues["price_inconsistency"] = {"count": int(bad.sum())}

        # Index checks
        if not isinstance(df.index, pd.DatetimeIndex):
            issues["index_type"] = {"msg": "index is not DatetimeIndex"}
        else:
            if not df.index.is_monotonic_increasing:
                issues["timestamp_order"] = {"msg": "index not monotonic increasing"}

        is_valid = (len(issues) == 0) or (not self.strict)
        return ValidationReport(is_valid, issues)
