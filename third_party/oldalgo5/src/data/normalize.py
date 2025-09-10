from __future__ import annotations

import pandas as pd

EXPECTED = ["open", "high", "low", "close", "volume"]

def _infer_cols(df: pd.DataFrame):
    cols = {c.lower(): c for c in df.columns}
    mapping = {}
    for k in EXPECTED:
        # accept both ohlcv and sometimes 'price' for close
        if k in cols:
            mapping[k] = cols[k]
        elif k == "close" and "price" in cols:
            mapping[k] = cols["price"]
        else:
            raise KeyError(f"normalize_ohlcv(): beklenen kolon eksik: {k}")
    return mapping

def normalize_ohlcv(df: pd.DataFrame, tz: str = "UTC", include_adj_close: bool = False, **kwargs) -> pd.DataFrame:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError("normalize_ohlcv(): geçersiz/boş DataFrame")
    # ensure index is datetime
    out = df.copy()
    if not isinstance(out.index, pd.DatetimeIndex):
        # try column named 'date' or 'datetime'
        if "date" in out.columns:
            out = out.set_index(pd.to_datetime(out["date"]))
        elif "datetime" in out.columns:
            out = out.set_index(pd.to_datetime(out["datetime"]))
        else:
            out.index = pd.to_datetime(out.index)
    out.index = out.index.tz_localize("UTC") if out.index.tz is None else out.index.tz_convert("UTC")
    mapping = _infer_cols(out)
    out = out[[mapping[k] for k in EXPECTED]]
    out.columns = EXPECTED
    out = out.sort_index()
    return out
