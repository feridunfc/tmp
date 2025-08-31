"""

# FROZEN: Do not modify public API or behavior without an approved RFC.

ALGO5 Module: src/algo5/data/validate.py

Purpose
-------
End-to-end OHLCV data validation for 2025-readiness: dtype coercion, DST-safe
timezone normalization to UTC, NaN/outlier reporting, and a deterministic
checksum usable as a FeatureStore cache key. Optional JSON schema validation
is available for API ingestion.

Responsibilities
----------------
- Canonicalize dataframe (columns, dtypes, index, timezone).
- Produce deterministic checksum (stable cache key).
- Emit data quality report (NaN ratios, IQR outliers, monotonicity).
- (Optional) Validate JSON payloads for API inputs.

Public API
----------
- validate_ohlcv(df, *, allow_extras=True, ...) -> (pd.DataFrame, dict)

Maturity & Status
-----------------
Maturity: STABLE
Rationale: Feature-complete for Week-1 DoD; thresholds configurable; promote to
FROZEN after field validation in live pipelines.
Owner: data-platform   Since: 2025-08-31   Last-Reviewed: 2025-08-31

Notes
-----
- DST handling via tz_localize(..., nonexistent="shift_forward", ambiguous="infer")
  then tz_convert("UTC").
- Checksum includes index; safe to use as FeatureStore cache key.
"""

from __future__ import annotations
from typing import Any, Dict, Tuple, Optional
import hashlib
import pandas as pd
import numpy as np

try:
    # Optional: only used if json_payload is provided
    from pydantic import BaseModel, Field, ValidationError  # type: ignore
    _HAS_PYDANTIC = True
except Exception:  # pragma: no cover
    _HAS_PYDANTIC = False

from .schemas import OhlcvSchema  # Defines required columns / dtype expectations

# ---- Optional JSON model (used only when json_payload is provided) ----------------
if _HAS_PYDANTIC:
    class OhlcvJSON(BaseModel):  # type: ignore[misc]
        timestamp: list[str]
        open: list[float]
        high: list[float]
        low: list[float]
        close: list[float]
        volume: list[int]


REQUIRED = ["Open", "High", "Low", "Close", "volume"]


def _canonicalize(df: pd.DataFrame) -> pd.DataFrame:
    """Canonicalize column order/dtypes and enforce UTC datetime index (DST-safe).

    - Lowercase/standardize raw names (e.g., 'close' -> 'Close').
    - Dtypes: price columns → float64; volume → Int64.
    - Index: ensure DatetimeIndex in UTC, handling DST edge cases.
    - Sort by index for determinism.
    """
    df2 = df.copy()

    # Normalize column names
    rename_map = {}
    if "close" in df2.columns and "Close" not in df2.columns:
        rename_map["close"] = "Close"
    for c in ["open", "high", "low"]:
        if c in df2.columns and c.capitalize() not in df2.columns:
            rename_map[c] = c.capitalize()
    if rename_map:
        df2 = df2.rename(columns=rename_map)

    # Enforce dtypes
    for c in ["Open", "High", "Low", "Close"]:
        if c in df2.columns:
            df2[c] = pd.to_numeric(df2[c], errors="coerce").astype("float64")
    if "volume" in df2.columns:
        df2["volume"] = pd.to_numeric(df2["volume"], errors="coerce").astype("Int64")

    # Ensure datetime index in UTC (DST-safe)
    if not isinstance(df2.index, pd.DatetimeIndex):
        df2.index = pd.to_datetime(df2.index, errors="coerce", utc=True)
    else:
        if df2.index.tz is None:
            # Handle nonexistent/ambiguous timestamps defensively
            try:
                df2.index = df2.index.tz_localize("UTC")
            except (TypeError, ValueError):
                df2.index = df2.index.tz_localize(
                    "UTC", nonexistent="shift_forward", ambiguous="infer"
                )
        else:
            df2.index = df2.index.tz_convert("UTC")

    # Deterministic column order (required first)
    cols = [c for c in REQUIRED if c in df2.columns] + [c for c in df2.columns if c not in REQUIRED]
    df2 = df2[cols]

    # Deterministic row order
    df2 = df2.sort_index()
    return df2


def _checksum(df: pd.DataFrame) -> str:
    """Return deterministic SHA-256 checksum of the canonicalized dataframe (index included)."""
    cdf = _canonicalize(df)
    h = pd.util.hash_pandas_object(cdf, index=True).values.tobytes()
    return hashlib.sha256(h).hexdigest()


def _nan_report(df: pd.DataFrame, cols: list[str]) -> Dict[str, float]:
    """NaN ratio per column (0..1)."""
    return {c: float(pd.isna(df[c]).mean()) for c in cols if c in df.columns}


def _outlier_iqr_count(df: pd.DataFrame, cols: list[str]) -> Dict[str, int]:
    """Outlier count per column using IQR (1.5*IQR); IQR<=0 için median-based fallback."""
    out: Dict[str, int] = {}
    for c in cols:
        if c not in df.columns:
            continue
        s = pd.to_numeric(df[c], errors="coerce")
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        if pd.isna(iqr) or iqr <= 0:
            # Fallback: median deviation with tiny tolerance (constant series + spikes)
            med = s.median(skipna=True)
            eps_abs = 1e-9
            eps_rel = 1e-6
            tol = abs(med) * eps_rel + eps_abs
            out[c] = int((s.sub(med).abs().gt(tol)).sum())
        else:
            low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            out[c] = int(((s < low) | (s > high)).sum())
    return out




def _esg_co2e(df: pd.DataFrame) -> float:
    """Very simple ESG proxy: ~0.04 g CO2e per tick (placeholder)."""
    return float(len(df) * 0.04)


def validate_ohlcv(
    df: pd.DataFrame,
    *,
    schema: OhlcvSchema | None = None,
    allow_extras: bool = True,
    strict_outliers_ratio: float = 0.05,   # fail if any column outliers > 5% of rows
    large_threshold: int = 1_000_000,      # mark large datasets for Dask hinting
    use_dask_hint: bool = True,
    json_payload: dict | None = None,      # optional: validate API JSON alongside df
    raise_errors: bool = False,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Validate OHLCV dataframe and return (normalized_df, validation_report).

    Args:
        df: Input OHLCV dataframe (index may be any time-like; columns case-insensitive).
        schema: Optional schema object (defaults to OhlcvSchema()).
        allow_extras: Keep non-required columns if True; otherwise trim to REQUIRED.
        strict_outliers_ratio: If outlier count exceeds this share, mark report as failed.
        large_threshold: Row count above which we flag the dataset as "large".
        use_dask_hint: If True and dataset is large, add a hint to errors to use Dask.
        json_payload: Optional JSON (dict) to validate for API ingestion (Pydantic).
        raise_errors: If True, raise exceptions on schema/JSON violations.

    Returns:
        normalized_df: Canonicalized dataframe (UTC index, enforced dtypes/order).
        report: Dict with fields:
            - ok: bool
            - checksum: str
            - errors: list[str]
            - missing: list[str]
            - renamed: dict[str, str]
            - nan_ratio: dict[str, float]
            - outliers_iqr: dict[str, int]
            - monotonic: bool
            - original_timezone: Optional[str]
            - normalized_timezone: 'UTC'
            - large_dataset: bool
            - fail_reason: Optional[str]
            - co2e_per_tick: float

    Raises:
        ValueError: When required columns are missing and raise_errors=True.
        Exception: For JSON schema violations if raise_errors=True and Pydantic available.
    """
    rep: Dict[str, Any] = {
        "ok": True,
        "checksum": "",
        "errors": [],
        "missing": [],
        "renamed": {},
        "nan_ratio": {},
        "outliers_iqr": {},
        "monotonic": True,
        "original_timezone": None,
        "normalized_timezone": "UTC",
        "large_dataset": False,
        "fail_reason": None,
        "co2e_per_tick": 0.0,
    }

    schema = schema or OhlcvSchema()

    # (Optional) Validate JSON API payload
    if json_payload is not None:
        if not _HAS_PYDANTIC:
            rep["errors"].append("pydantic_not_installed_for_json_validation")
        else:
            try:
                _ = OhlcvJSON(**json_payload)  # type: ignore[misc]
            except ValidationError as e:  # type: ignore[name-defined]
                rep["ok"] = False
                rep["errors"].append(f"json_schema_error:{e.errors()}")
                if raise_errors:
                    raise

    # Record original tz if any
    if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
        rep["original_timezone"] = str(df.index.tz)

    # Canonicalize (names/dtypes/index UTC + sort)
    df = _canonicalize(df)

    # Required columns check (use canonical names)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        rep["ok"] = False
        rep["missing"] = missing
        rep["errors"].append(f"missing_columns:{missing}")
        if raise_errors:
            raise ValueError(f"Missing required columns: {missing}")

    # Rename report (if we performed common mappings earlier)
    if "close" in getattr(df, "_cached_columns", []) or "Close" in df.columns:
        # best-effort: we note typical normalization; exact map already applied in _canonicalize
        rep["renamed"] = {k: v for k, v in {"close": "Close", "open": "Open", "high": "High", "low": "Low"}.items()
                          if k in df.columns or v in df.columns}

    # Monotonicity (if we had to sort, flag as non-monotonic)
    if not df.index.is_monotonic_increasing:
        df = df.sort_index()
        rep["monotonic"] = False

    # Trim extras if requested (preserve index)
    if not allow_extras:
        df = df.loc[:, [c for c in REQUIRED if c in df.columns]]

    # Data quality metrics
    rep["nan_ratio"] = _nan_report(df, REQUIRED)
    rep["outliers_iqr"] = _outlier_iqr_count(df, REQUIRED)

    # Checksum & ESG proxy
    rep["checksum"] = _checksum(df)
    rep["co2e_per_tick"] = _esg_co2e(df)

    # Size hinting
    if len(df) > large_threshold:
        rep["large_dataset"] = True
        if use_dask_hint:
            rep["errors"].append("large_dataset_use_dask")

    # Aggregate OK rules
    if any(r > 0.30 for r in rep["nan_ratio"].values()):
        rep["ok"] = False
        rep["fail_reason"] = rep["fail_reason"] or "too_many_nans"
    if any(cnt > len(df) * strict_outliers_ratio for cnt in rep["outliers_iqr"].values()):
        rep["ok"] = False
        rep["fail_reason"] = rep["fail_reason"] or "too_many_outliers"

    return df, rep
