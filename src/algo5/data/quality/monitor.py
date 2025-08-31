"""
ALGO5 Module: src/algo5/data/quality/monitor.py

Purpose
-------
Run data quality checks (2025-ready validator), persist a JSON audit report, and
export observability metrics to Prometheus (NaN/outlier, ESG proxy, size hints).

Responsibilities
----------------
- Execute validate_ohlcv and enrich the report with checksum and quick stats.
- Persist JSON report safely to disk (guard against path issues).
- Export metrics: dq_errors_total, dq_nan_ratio{column}, dq_outliers_iqr{column},
  dq_large_dataset (rows), dq_co2e_per_tick (g).

Public API
----------
- DataQualityMonitor(...).run(df) -> dict

Maturity & Status
-----------------
Maturity: STABLE
Rationale: Meets Week-1 DoD + 2025 requirements (ESG, size/gauge, safety).
Owner: observability    Since: 2025-08-31    Last-Reviewed: 2025-08-31

Notes
-----
- Prometheus is optional; module works without it.
- Consider cardinality impact when adding metric labels.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional
import json
import logging
from pathlib import Path

import pandas as pd

from ..integrity import df_checksum
from ..validate import validate_ohlcv
from ..schemas import OhlcvSchema

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Gauge
    _PROM = True
    # Global metrics (avoid re-creating on each call)
    dq_errors = Counter("dq_errors_total", "Data quality errors")
    nan_ratio_g = Gauge("dq_nan_ratio", "NaN ratio", ["column"])
    outlier_cnt_g = Gauge("dq_outliers_iqr", "Outlier count (IQR)", ["column"])
    large_rows_g = Gauge("dq_large_dataset", "Row count (dataset size)")
    co2e_g = Gauge("dq_co2e_per_tick", "CO2e proxy (g)")
except ImportError:  # only disable on import errors
    _PROM = False


@dataclass
class DataQualityMonitor:
    """
    Run the 2025-ready validator, write a JSON report, and export Prometheus metrics.

    Args:
        out_path: Where to write the report (None = do not write).
        schema: Optional schema for validation.
        allow_extras: Keep non-required columns if True; else trim to required.
        raise_errors: Raise on validation failures (usually False for monitoring).
        strict_outliers_ratio: Mark report as failed if outliers exceed this share.
        large_threshold: Row-count threshold to flag "large dataset".
        use_dask_hint: If True and dataset is large, add a 'use_dask' hint to errors.
        base_dir: Optional directory constraint for safe writes; if provided,
                  the out_path must resolve under this directory.

    Returns:
        Dict validation report with checksum, ESG proxy, size flags, and DQ metrics.
    """
    out_path: Optional[str] = "dq_report.json"
    schema: Optional[OhlcvSchema] = None
    allow_extras: bool = True
    raise_errors: bool = False
    strict_outliers_ratio: float = 0.05
    large_threshold: int = 1_000_000
    use_dask_hint: bool = True
    base_dir: Optional[Path] = None

    def _safe_write(self, rep: Dict[str, Any]) -> None:
        """Safely write JSON report respecting base_dir (if set)."""
        if not self.out_path:
            return
        path = Path(self.out_path)

        # If a base_dir is configured, enforce that target is under it
        if self.base_dir is not None:
            base = self.base_dir.resolve()
            target = path.resolve()
            if not str(target).startswith(str(base)):
                raise PermissionError(f"Refusing to write outside base_dir: {target} !~ {base}")

        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)

    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate `df`, persist JSON (optional), and export Prometheus metrics."""
        df2, rep = validate_ohlcv(
            df,
            schema=self.schema,
            allow_extras=self.allow_extras,
            strict_outliers_ratio=self.strict_outliers_ratio,
            large_threshold=self.large_threshold,
            use_dask_hint=self.use_dask_hint,
            raise_errors=self.raise_errors,
        )

        # Enrich report with checksum (normalized frame) and quick stats
        rep["checksum"] = df_checksum(df2)
        rep.setdefault("stats", {})
        rep["stats"].update({
            "rows": int(len(df2)),
            "columns": int(len(df2.columns)),
            "date_range": (
                {
                    "start": df2.index.min().isoformat(),
                    "end": df2.index.max().isoformat(),
                } if not df2.empty else {}
            ),
        })

        # Persist JSON (safely)
        try:
            self._safe_write(rep)
        except PermissionError as e:
            logger.error("Failed to write DQ report to %s: %s", self.out_path, e)
            raise
        except Exception as e:
            logger.error("Failed to write DQ report to %s: %s", self.out_path, e)
        # Back-compat: expose schema info under "SchemaCheck" (for older tests/dashboards)

        try:
            schema_obj = self.schema or OhlcvSchema()
            _, mism = schema_obj.validate_dtypes(df2)
            rep["SchemaCheck"] = {
                "missing": [c for c in schema_obj.required if c not in df2.columns],
                "dtype_mismatches": mism,
            }
        except Exception:
            # optional: if schema not available, still expose at least missing from main report
            rep["SchemaCheck"] = {
                "missing": rep.get("missing", []),
                "dtype_mismatches": {},
            }

        # Prometheus metrics
        if _PROM:
            try:
                if not rep.get("ok", True) or rep.get("missing"):
                    dq_errors.inc()

                for col, ratio in rep.get("nan_ratio", {}).items():
                    try:
                        nan_ratio_g.labels(column=col).set(float(ratio))
                    except Exception as e:
                        logger.error("nan_ratio set failed for %s: %s", col, e)

                for col, count in rep.get("outliers_iqr", {}).items():
                    try:
                        outlier_cnt_g.labels(column=col).set(float(count))
                    except Exception as e:
                        logger.error("outliers_iqr set failed for %s: %s", col, e)

                # ESG proxy (g) + large dataset gauge
                co2e_val = float(rep.get("co2e_per_tick", 0.0))
                co2e_g.set(co2e_val)

                total_rows = int(rep.get("stats", {}).get("rows", len(df2)))
                if total_rows > self.large_threshold:
                    large_rows_g.set(total_rows)
                else:
                    # optional: reset to 0 to avoid stale non-zero
                    large_rows_g.set(0)
            except Exception as e:
                logger.error("Prometheus export failed: %s", e)

        # Log a warning if quality is poor
        if not rep.get("ok", True):
            logger.warning("Data quality issues detected. Report summary: %s", {
                "fail_reason": rep.get("fail_reason"),
                "nan_ratio": rep.get("nan_ratio"),
                "outliers_iqr": rep.get("outliers_iqr"),
            })

        return rep
