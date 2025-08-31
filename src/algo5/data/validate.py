from typing import Any, Dict, Tuple
import pandas as pd
from .schemas import OhlcvSchema


def validate_ohlcv(
    df: pd.DataFrame, *, schema: OhlcvSchema | None = None, raise_errors: bool = True
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    schema = schema or OhlcvSchema()
    report: Dict[str, Any] = {"ok": True, "missing": [], "renamed": {}}
    cols_lower = {c.lower(): c for c in df.columns}
    if "close" in cols_lower and "Close" not in df.columns:
        df = df.rename(columns={cols_lower["close"]: "Close"})
        report["renamed"]["close"] = "Close"
    missing = [c for c in schema.required if c not in df.columns]
    if missing:
        report["ok"] = False
        report["missing"] = missing
        if raise_errors:
            raise ValueError(f"Missing required columns: {missing}")
    report["nan_counts"] = {c: int(df[c].isna().sum()) for c in df.columns if c in df}
    return df, report
