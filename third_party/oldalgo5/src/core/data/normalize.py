import pandas as pd

def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        raise ValueError("normalize_ohlcv: input DataFrame is empty or None")
    _df = df.copy()
    # standardize column names
    rename = {c: str(c).lower() for c in _df.columns}
    _df = _df.rename(columns=rename)
    required = ["open","high","low","close","volume"]
    for k in required:
        if k not in _df.columns:
            raise KeyError(f"normalize_ohlcv: missing column '{k}' after rename")
    _df = _df[required]
    idx = pd.to_datetime(_df.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    else:
        idx = idx.tz_convert("UTC")
    _df.index = idx
    _df = _df.sort_index()
    return _df
