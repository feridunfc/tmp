from __future__ import annotations

from typing import Iterable
import pandas as pd


def ensure_utc_index(index: pd.Index) -> pd.DatetimeIndex:
    idx = pd.DatetimeIndex(index)
    if idx.tz is None:
        return idx.tz_localize("UTC")
    return idx.tz_convert("UTC")


def ensure_utc_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.index = ensure_utc_index(out.index)
    return out


_CANON = {
    "open": "open",
    "o": "open",
    "high": "high",
    "h": "high",
    "low": "low",
    "l": "low",
    "close": "close",
    "c": "close",
    "adj_close": "close",
    "adjclose": "close",
    "volume": "volume",
    "vol": "volume",
    "v": "volume",
}


def normalize_ohlcv(
    df: pd.DataFrame,
    required: Iterable[str] = ("open", "high", "low", "close"),
    tz: str = "UTC",
) -> pd.DataFrame:
    if df is None or df.empty:
        raise ValueError("normalize_ohlcv: empty df")

    # Kolon isimlerini kanonikleştir
    cols = {str(c): _CANON.get(str(c).lower(), str(c).lower()) for c in df.columns}
    out = df.rename(columns=cols).copy()

    # Volume yoksa ekle
    if "volume" not in out.columns:
        out["volume"] = 0.0

    # Sadece gerekli kolonları tut
    keep = [c for c in ("open", "high", "low", "close", "volume") if c in out.columns]
    out = out[keep]

    # Sayısal tiplere çevir
    for c in keep:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    # OHLC içinde NaN olan satırları at
    out = out.dropna(subset=["open", "high", "low", "close"], how="any")

    # Index'i UTC DatetimeIndex yap
    out.index = ensure_utc_index(out.index)

    # Index'i sırala, tekrarı at
    out = out[~out.index.duplicated(keep="last")].sort_index()

    # OHLC tutarlılığı: high=max(o,h,c), low=min(o,l,c)
    if {"open", "high", "low", "close"}.issubset(out.columns):
        oh = out[["open", "high", "low", "close"]]
        out["high"] = oh.max(axis=1)
        out["low"] = oh.min(axis=1)

    # İstenen zorunlu kolonlar var mı?
    missing = set(required) - set(out.columns)
    if missing:
        raise ValueError(f"normalize_ohlcv: missing required columns: {missing}")

    return out


__all__ = ["ensure_utc_index", "ensure_utc_df", "normalize_ohlcv"]
