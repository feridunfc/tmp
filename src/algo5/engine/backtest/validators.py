from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

REQUIRED_COLS_BASE = ("Open", "High", "Low", "Close")


@dataclass(frozen=True)
class OHLCVSpec:
    require_volume: bool = False
    allow_na: bool = False
    require_tz: bool = True  # UTC önerilir


def _has_required_columns(df: pd.DataFrame, require_volume: bool) -> bool:
    need = set(REQUIRED_COLS_BASE) | ({"Volume"} if require_volume else set())
    return need.issubset(set(df.columns))


def validate_ohlcv(df: pd.DataFrame, *, spec: OHLCVSpec | None = None) -> None:
    spec = spec or OHLCVSpec()
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("index must be a DatetimeIndex")
    if len(df.index) == 0:
        raise ValueError("dataframe is empty")
    if df.index.tz is None and spec.require_tz:
        raise ValueError("index must be timezone-aware (UTC recommended)")
    if not _has_required_columns(df, spec.require_volume):
        raise ValueError("missing required OHLC(V) columns")
    req = list(REQUIRED_COLS_BASE) + (["Volume"] if spec.require_volume else [])
    if not spec.allow_na and df[req].isna().any().any():
        raise ValueError("NaNs not allowed in required columns")
    if (df["Low"] > df["High"]).any():
        raise ValueError("Low cannot be greater than High")


def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    if isinstance(out.index, pd.DatetimeIndex) and out.index.tz is None:
        out.index = out.index.tz_localize("UTC")
    return out


__all__ = ["OHLCVSpec", "validate_ohlcv", "normalize_ohlcv"]
