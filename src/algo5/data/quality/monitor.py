from __future__ import annotations
import pandas as pd
from dataclasses import dataclass
from typing import Dict, Any, Iterable
from ..schemas import OhlcvSchema

@dataclass
class SchemaCheck:
    required: tuple[str, ...] = OhlcvSchema().required
    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        missing = sorted(set(self.required) - set(df.columns))
        return {"ok": not missing, "missing": missing}

@dataclass
class NaNCheck:
    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        nans = df.isna().sum().to_dict()
        total = int(df.isna().sum().sum())
        return {"ok": total == 0, "by_column": nans, "total": total}

class DataQualityMonitor:
    def __init__(self, checks: Iterable[object] | None = None):
        self.checks = list(checks or [SchemaCheck(), NaNCheck()])

    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        report: Dict[str, Any] = {}
        for chk in self.checks:
            report[chk.__class__.__name__] = chk.run(df)
        report["ok"] = all(v.get("ok", True) for v in report.values())
        return report
