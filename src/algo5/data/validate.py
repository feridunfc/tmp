from __future__ import annotations

from typing import Any, Dict, Tuple

import pandas as pd

from .schemas import OhlcvSchema


def validate_ohlcv(
    df: pd.DataFrame,
    *,
    schema: OhlcvSchema | None = None,
    allow_extras: bool = True,
    raise_errors: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    schema = schema or OhlcvSchema()
    required = set(schema.required)
    if allow_extras is None:
        allow_extras = schema.allow_extras

    report: Dict[str, Any] = {"ok": True, "missing": [], "renamed": {}}

    # normalize common lowercase 'close' -> 'Close'
    if "close" in df.columns and "Close" not in df.columns:
        df = df.rename(columns={"close": "Close"})
        report["renamed"]["close"] = "Close"

    missing = sorted(required - set(df.columns))
    if missing:
        report["ok"] = False
        report["missing"] = missing
        if raise_errors:
            raise ValueError(f"Missing required columns: {missing}")

    # ensure index sorted
    if not df.index.is_monotonic_increasing:
        df = df.sort_index()

    return df, report
