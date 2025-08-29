
from __future__ import annotations
from typing import Any, Dict, Tuple
import pandas as pd

REQ = ["Open","High","Low","Close","Volume"]

def validate_ohlcv(
    df: pd.DataFrame,
    *,
    allow_extras: bool = True,
    raise_errors: bool = True
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    d = df.copy()
    # normalize lowercase 'close' to 'Close'
    lower = {c.lower(): c for c in d.columns}
    if "close" in lower and "Close" not in d.columns:
        d = d.rename(columns={lower["close"]: "Close"})
    missing = set(REQ) - set(d.columns)
    report = {"ok": len(missing) == 0, "missing": sorted(missing)}
    if missing and raise_errors:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    return d, report
