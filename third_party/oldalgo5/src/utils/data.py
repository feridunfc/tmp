#
# # -*- coding: utf-8 -*-
# """Robust OHLCV normalization helpers (v2.10)
# - Accepts various column casings (Open/open, Close/Adj Close, Volume, ...)
# - Handles MultiIndex columns by flattening
# - Ensures DatetimeIndex in UTC and sorted/unique
# - Returns a DataFrame that contains both lowercase and Title-Case aliases
#   (e.g. 'close' and 'Close') so legacy strategies won't break.
# """
# from __future__ import annotations
# import re
# import pandas as pd
# import numpy as np
# from typing import Iterable, Dict
#
# __all__ = ["normalize_ohlcv", "ensure_datetime_utc"]
#
# def ensure_datetime_utc(idx) -> pd.DatetimeIndex:
#     if not isinstance(idx, pd.DatetimeIndex):
#         try:
#             idx = pd.to_datetime(idx, utc=True)
#         except Exception:
#             # fallback: treat as range-index timestamps
#             idx = pd.to_datetime(pd.Index(idx), utc=True, errors="coerce")
#     else:
#         # make sure tz-aware in UTC
#         if idx.tz is None:
#             idx = idx.tz_localize("UTC")
#         else:
#             idx = idx.tz_convert("UTC")
#     # sort & drop duplicates
#     idx = pd.DatetimeIndex(idx).sort_values()
#     idx = idx[~idx.duplicated(keep="first")]
#     return idx
#
# def _flatten_columns(cols: Iterable) -> Iterable[str]:
#     # Turn MultiIndex to single level with '_' join. Strip spaces.
#     out = []
#     for c in cols:
#         if isinstance(c, tuple):
#             name = "_".join([str(x) for x in c if x is not None])
#         else:
#             name = str(c)
#         out.append(name)
#     return out
#
# def _canon(s: str) -> str:
#     # normalize strings for matching
#     s = s.lower().strip()
#     s = s.replace(" ", "").replace("_", "")
#     s = re.sub(r"[^a-z0-9]", "", s)
#     return s
# # src/algo2/utils/data.py
# import pandas as pd
# import numpy as np
#
# __all__ = ["demo_ohlcv", "normalize_ohlcv", "resample_ohlcv", "to_returns"]
#
# def demo_ohlcv(symbols: str = "AAPL,MSFT", bars: int = 600, seed: int = 7) -> pd.DataFrame:
#     """Deterministik sentetik OHLCV üretir. Index: DatetimeIndex; kolonlar: Open,High,Low,Close,Volume,Symbol"""
#     rng = np.random.default_rng(seed)
#     end = pd.Timestamp.today().normalize()
#     idx = pd.date_range(end=end, periods=bars, freq="B")
#     frames = []
#     for sym in [s.strip() for s in str(symbols).split(",") if s.strip()]:
#         ret = rng.normal(0.0003, 0.01, len(idx))
#         price = 100 * (1 + pd.Series(ret, index=idx)).cumprod()
#         high = price * (1 + rng.uniform(0.0, 0.01, len(idx)))
#         low  = price * (1 - rng.uniform(0.0, 0.01, len(idx)))
#         openp = price.shift(1).fillna(price.iloc[0])
#         vol = rng.integers(2e5, 8e5, len(idx))
#         df = pd.DataFrame({"Open": openp, "High": high, "Low": low, "Close": price, "Volume": vol}, index=idx)
#         df["Symbol"] = sym
#         frames.append(df)
#     out = pd.concat(frames, axis=0).sort_index()
#     out.index.name = "Date"
#     return out
#
# def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
#     """Index'i DatetimeIndex'e çevirir, sütun adlarını standardize eder, tipleri sayısal yapar."""
#     if not isinstance(df.index, pd.DatetimeIndex):
#         if "Date" in df.columns:
#             df = df.set_index(pd.to_datetime(df["Date"]))
#         else:
#             raise TypeError("Input must have DatetimeIndex or a 'Date' column.")
#     # sütun isimleri (lower-case'leri standarda çevir)
#     canon = {"open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume","symbol":"Symbol"}
#     df = df.rename(columns={c: canon.get(str(c).lower(), c) for c in df.columns})
#     req = ["Open","High","Low","Close","Volume"]
#     missing = [c for c in req if c not in df.columns]
#     if missing:
#         raise ValueError(f"Missing OHLCV columns: {missing}")
#     # sayısal tiplere döndür
#     for c in ["Open","High","Low","Close","Volume"]:
#         df[c] = pd.to_numeric(df[c], errors="coerce")
#     if "Symbol" not in df.columns:
#         df["Symbol"] = "UNKNOWN"
#     return df.sort_index()
#
# def resample_ohlcv(df: pd.DataFrame, rule: str = "1D") -> pd.DataFrame:
#     """Sembol bazında yeniden örnekleme (OHLCV)."""
#     df = normalize_ohlcv(df)
#     agg_map = {"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}
#     frames = []
#     for sym, g in df.groupby("Symbol", group_keys=False):
#         r = g.resample(rule).agg(agg_map).dropna(how="any")
#         r["Symbol"] = sym
#         frames.append(r)
#     out = pd.concat(frames, axis=0).sort_index()
#     out.index.name = "Date"
#     return out
#
# def to_returns(px: pd.Series) -> pd.Series:
#     """Basit log-olmayan getiriler (pct_change)."""
#     return pd.to_numeric(px, errors="coerce").pct_change().fillna(0.0)
#
# # def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
# #     """Return a normalized OHLCV frame with both lowercase and Title-Case aliases.
# #
# #     The canonical set:
# #         ['open','high','low','close','volume']
# #     will always exist. Additionally, Title-Case aliases:
# #         ['Open','High','Low','Close','Volume']
# #     are created as views/copies to maximize backward compatibility.
# #     """
# #     if df is None or len(df) == 0:
# #         return pd.DataFrame(columns=["open","high","low","close","volume"])
# #
# #     x = df.copy(deep=False)
# #     # flatten columns if needed
# #     try:
# #         if hasattr(x, "columns") and getattr(x.columns, "nlevels", 1) > 1:
# #             x.columns = _flatten_columns(x.columns)
# #     except Exception:
# #         pass
# #
# #     # build mapping by canonical name
# #     # include common variants and abbreviations
# #     variants: Dict[str, set] = {
# #         "open": {"open", "o", "opn", "openingprice"},
# #         "high": {"high", "h", "max", "hi"},
# #         "low":  {"low", "l", "min", "lo"},
# #         "close": {"close", "c", "cls", "last", "price", "adjclose", "adjustedclose"},
# #         "volume": {"volume", "vol", "v", "qty", "amount"}
# #     }
# #
# #     cols = list(x.columns)
# #     canon_map: Dict[str, str] = {}  # canon -> real column name
# #
# #     # First pass: direct exact matches ignoring case
# #     low_cols = {_canon(c): c for c in cols}
# #
# #     for canon, names in variants.items():
# #         found = None
# #         # prefer exact field (close over adjclose, etc.)
# #         for key in [canon] + sorted(list(names - {canon})):
# #             if key in low_cols:
# #                 real = low_cols[key]
# #                 # if we matched 'adjclose' for close but a 'close' also exists, keep 'close'
# #                 if canon == "close" and "close" in low_cols:
# #                     real = low_cols["close"]
# #                 found = real
# #                 break
# #         # special: yfinance uses 'Adj Close'
# #         if found is None and canon == "close":
# #             for k in ("adjclose", "adjustedclose"):
# #                 if k in low_cols:
# #                     found = low_cols[k]
# #                     break
# #             if found is None:
# #                 # look for 'adj_close' style
# #                 for c in cols:
# #                     if _canon(c) in ("adjclose", "adjustedclose", "adjcloseprice"):
# #                         found = c
# #                         break
# #         if found is not None:
# #             canon_map[canon] = found
# #
# #     # if anything missing, try heuristic by first char
# #     if "open" not in canon_map:
# #         for c in cols:
# #             if _canon(c).startswith("open"):
# #                 canon_map["open"] = c; break
# #     if "high" not in canon_map:
# #         for c in cols:
# #             if _canon(c).startswith("high"):
# #                 canon_map["high"] = c; break
# #     if "low" not in canon_map:
# #         for c in cols:
# #             if _canon(c).startswith("low"):
# #                 canon_map["low"] = c; break
# #     if "close" not in canon_map:
# #         for c in cols:
# #             cc = _canon(c)
# #             if cc.startswith("close") or cc.startswith("cls") or cc.startswith("last"):
# #                 canon_map["close"] = c; break
# #     if "volume" not in canon_map:
# #         for c in cols:
# #             if _canon(c).startswith("vol"):
# #                 canon_map["volume"] = c; break
# #
# #     # Build the output
# #     out = pd.DataFrame(index=ensure_datetime_utc(x.index))
# #     for canon in ["open","high","low","close","volume"]:
# #         src = canon_map.get(canon)
# #         if src is not None and src in x.columns:
# #             out[canon] = pd.to_numeric(x[src], errors="coerce")
# #         else:
# #             # if truly missing, fill zeros for volume, fwd-fill for prices
# #             if canon == "volume":
# #                 out[canon] = 0.0
# #             else:
# #                 # try best-effort from other similar columns
# #                 out[canon] = pd.to_numeric(x[x.columns[0]], errors="coerce") if len(x.columns)>0 else np.nan
# #
# #     # basic cleaning
# #     out = out.sort_index()
# #     out = out[~out.index.duplicated(keep="first")]
# #     # Forward-fill missing price fields, keep volume NaN->0
# #     for fld in ["open","high","low","close"]:
# #         out[fld] = out[fld].astype(float).replace([np.inf, -np.inf], np.nan).ffill()
# #     out["volume"] = out["volume"].astype(float).replace([np.inf, -np.inf, np.nan], 0.0)
# #
# #     # Create Title-Case aliases for legacy code
# #     alias = {"open":"Open", "high":"High", "low":"Low", "close":"Close", "volume":"Volume"}
# #     for k, K in alias.items():
# #         out[K] = out[k]
# #
# #     return out


# src/algo2/utils/data.py
import pandas as pd
import numpy as np

__all__ = ["demo_ohlcv", "normalize_ohlcv", "resample_ohlcv", "to_returns"]

def demo_ohlcv(symbols: str = "AAPL,MSFT", bars: int = 600, seed: int = 7) -> pd.DataFrame:
    """Deterministik sentetik OHLCV üretir. Index: DatetimeIndex; kolonlar: Open,High,Low,Close,Volume,Symbol"""
    rng = np.random.default_rng(seed)
    end = pd.Timestamp.today().normalize()
    idx = pd.date_range(end=end, periods=bars, freq="B")
    frames = []
    for sym in [s.strip() for s in str(symbols).split(",") if s.strip()]:
        ret = rng.normal(0.0003, 0.01, len(idx))
        price = 100 * (1 + pd.Series(ret, index=idx)).cumprod()
        high = price * (1 + rng.uniform(0.0, 0.01, len(idx)))
        low  = price * (1 - rng.uniform(0.0, 0.01, len(idx)))
        openp = price.shift(1).fillna(price.iloc[0])
        vol = rng.integers(2e5, 8e5, len(idx))
        df = pd.DataFrame({"Open": openp, "High": high, "Low": low, "Close": price, "Volume": vol}, index=idx)
        df["Symbol"] = sym
        frames.append(df)
    out = pd.concat(frames, axis=0).sort_index()
    out.index.name = "Date"
    return out

def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Index'i DatetimeIndex'e çevirir, sütun adlarını standardize eder, tipleri sayısal yapar."""
    if not isinstance(df.index, pd.DatetimeIndex):
        if "Date" in df.columns:
            df = df.set_index(pd.to_datetime(df["Date"]))
        else:
            raise TypeError("Input must have DatetimeIndex or a 'Date' column.")
    # sütun isimleri (lower-case'leri standarda çevir)
    canon = {"open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume","symbol":"Symbol"}
    df = df.rename(columns={c: canon.get(str(c).lower(), c) for c in df.columns})
    req = ["Open","High","Low","Close","Volume"]
    missing = [c for c in req if c not in df.columns]
    if missing:
        raise ValueError(f"Missing OHLCV columns: {missing}")
    # sayısal tiplere döndür
    for c in ["Open","High","Low","Close","Volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if "Symbol" not in df.columns:
        df["Symbol"] = "UNKNOWN"
    return df.sort_index()

def resample_ohlcv(df: pd.DataFrame, rule: str = "1D") -> pd.DataFrame:
    """Sembol bazında yeniden örnekleme (OHLCV)."""
    df = normalize_ohlcv(df)
    agg_map = {"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}
    frames = []
    for sym, g in df.groupby("Symbol", group_keys=False):
        r = g.resample(rule).agg(agg_map).dropna(how="any")
        r["Symbol"] = sym
        frames.append(r)
    out = pd.concat(frames, axis=0).sort_index()
    out.index.name = "Date"
    return out

def to_returns(px: pd.Series) -> pd.Series:
    """Basit log-olmayan getiriler (pct_change)."""
    return pd.to_numeric(px, errors="coerce").pct_change().fillna(0.0)
