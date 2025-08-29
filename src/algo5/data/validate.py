from __future__ import annotations
import pandas as pd
from typing import Any, Dict, Tuple
from .schemas import OhlcvSchema

def validate_ohlcv(
    df: pd.DataFrame,
    *,
    schema: OhlcvSchema = OhlcvSchema(),
    raise_errors: bool = True,
    allow_extras: bool | None = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    if allow_extras is None:
        allow_extras = schema.allow_extras
    report: Dict[str, Any] = {"ok": True, "missing": [], "renamed": {}}
    cols = list(df.columns)

    # normalize common lowercase 'close'
    if "close" in df.columns and "Close" not in df.columns:
        df = df.rename(columns={"close": "Close"})
        report["renamed"]["close"] = "Close"

    missing = [c for c in schema.required if c not in df.columns]
    if missing:
        report["ok"] = False
        report["missing"] = missing
        if raise_errors:
            raise ValueError(f"Missing required columns: {missing}")

    # sort index & ensure monotonic
    if not df.index.is_monotonic_increasing:
        df = df.sort_index()

    return df, report
