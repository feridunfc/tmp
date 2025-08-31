"""
ALGO5 Module: src/algo5/data/schemas.py

Purpose
-------
Typed, versioned schemas for OHLCV and related data, with optional JSON Schema
export for API contracts. Keeps validate.py consistent by canonicalizing names
and enforcing pandas dtypes (float64/Int64).

Responsibilities
----------------
- Define required columns and canonical pandas dtypes.
- Provide helpers to validate/coerce dtypes and normalize column names.
- Optionally export Pydantic JSON Schemas for records & list payloads.
- Allow future extensions (ESG, metadata).

Public API
----------
- OhlcvSchema(required, allow_extras, dtypes)
  - canonicalize_columns(df) -> pd.DataFrame
  - validate_dtypes(df) -> (ok: bool, mismatches: dict)
  - coerce_dtypes(df) -> (df2, report: dict)
  - as_pandas_dtype_map() -> dict[str, str]
  - json_record_model() / json_payload_model()  # if pydantic installed
  - json_record_schema() / json_payload_schema() -> dict
  - version

Maturity & Status
-----------------
Maturity: STABLE
Rationale: Aligns with Week-1 FROZEN validator; provides JSON schema hooks.
Owner: data-platform   Since: 2025-08-31   Last-Reviewed: 2025-08-31

Notes
-----
- Canonical columns: "Open","High","Low","Close","volume" (lowercase volume).
- Pandas dtypes: prices float64, volume Int64 (nullable).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

import pandas as pd

__all__ = [
    "OhlcvSchema",
]

_SCHEMAS_VERSION = "1.0.0"  # bump on breaking schema changes


def _default_dtypes() -> Dict[str, str]:
    # Prices as float64; volume as nullable Int64 (pandas NA-aware integer)
    return {
        "Open": "float64",
        "High": "float64",
        "Low": "float64",
        "Close": "float64",
        "volume": "Int64",
    }


@dataclass
class OhlcvSchema:
    """OHLCV schema with dtype expectations and helpers."""

    required: Tuple[str, ...] = ("Open", "High", "Low", "Close", "volume")
    allow_extras: bool = True
    dtypes: Dict[str, str] = field(default_factory=_default_dtypes)
    version: str = _SCHEMAS_VERSION

    # --- Column canonicalization -------------------------------------------------

    @staticmethod
    def canonicalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Rename common variants to canonical names used across ALGO5.

        - 'open','high','low' -> 'Open','High','Low'
        - 'close' -> 'Close'
        - 'Volume' -> 'volume' (lowercase)
        """
        rename: Dict[str, str] = {}
        for raw, canon in (("open", "Open"), ("high", "High"), ("low", "Low"), ("close", "Close")):
            if raw in df.columns and canon not in df.columns:
                rename[raw] = canon
        if "Volume" in df.columns and "volume" not in df.columns:
            rename["Volume"] = "volume"
        if rename:
            df = df.rename(columns=rename)
        return df

    # --- Dtype validation/coercion ----------------------------------------------

    def as_pandas_dtype_map(self) -> Dict[str, str]:
        """Return canonical pandas dtype mapping for required columns."""
        return dict(self.dtypes)

    def validate_dtypes(self, df: pd.DataFrame) -> Tuple[bool, Dict[str, str]]:
        """Check if df dtypes match schema dtypes (only for present required cols)."""
        mismatches: Dict[str, str] = {}
        for col, expected in self.dtypes.items():
            if col in df.columns:
                actual = str(df[col].dtype)
                if actual != expected:
                    mismatches[col] = f"{actual} != {expected}"
        return (len(mismatches) == 0, mismatches)

    def coerce_dtypes(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Coerce df to schema dtypes where possible. Returns (df2, report)."""
        df2 = df.copy()
        report: Dict[str, Any] = {"coerced": {}, "missing": []}

        # Ensure canonical column names first
        df2 = self.canonicalize_columns(df2)

        for col in self.required:
            if col not in df2.columns:
                report["missing"].append(col)
                continue
            target = self.dtypes.get(col)
            if target is None:
                continue

            if target == "Int64":
                df2[col] = pd.to_numeric(df2[col], errors="coerce").astype("Int64")
                report["coerced"][col] = "Int64"
            else:
                # default: numeric float-like
                df2[col] = pd.to_numeric(df2[col], errors="coerce").astype(target)
                report["coerced"][col] = target

        return df2, report

    # --- Optional: Pydantic JSON schema -----------------------------------------

    @staticmethod
    def _require_pydantic():
        try:
            from pydantic import BaseModel  # type: ignore
            return BaseModel
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "pydantic is required for JSON schema export; please install it."
            ) from e

    def json_record_model(self):
        """Return a Pydantic model for a single OHLCV record (with ESG/metadata)."""
        BaseModel = self._require_pydantic()  # noqa: N806

        class OhlcvRecord(BaseModel):  # type: ignore
            timestamp: str
            Open: float
            High: float
            Low: float
            Close: float
            volume: int
            ESG: Optional[Dict[str, Any]] = None
            metadata: Optional[Dict[str, Any]] = None

        OhlcvRecord.__name__ = "OhlcvRecord"
        return OhlcvRecord

    def json_payload_model(self):
        """Return a Pydantic model for a batched OHLCV payload (column lists)."""
        BaseModel = self._require_pydantic()  # noqa: N806

        class OhlcvPayload(BaseModel):  # type: ignore
            timestamp: list[str]
            open: list[float]
            high: list[float]
            low: list[float]
            close: list[float]
            volume: list[int]
            ESG: Optional[Dict[str, Any]] = None
            metadata: Optional[Dict[str, Any]] = None

        OhlcvPayload.__name__ = "OhlcvPayload"
        return OhlcvPayload

    def json_record_schema(self) -> Dict[str, Any]:
        """JSON Schema dict for a single record."""
        Model = self.json_record_model()
        return Model.model_json_schema()  # pydantic v2

    def json_payload_schema(self) -> Dict[str, Any]:
        """JSON Schema dict for a list payload."""
        Model = self.json_payload_model()
        return Model.model_json_schema()  # pydantic v2
