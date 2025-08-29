from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import pandas as pd

from ..integrity import df_checksum


@dataclass
class SchemaCheck:
    required: tuple = ("Open", "High", "Low", "Close", "Volume")

    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        missing = sorted(set(self.required) - set(df.columns))
        return {"ok": not missing, "missing": missing}


class DataQualityMonitor:
    def __init__(self, checks=(SchemaCheck(),)) -> None:
        self.checks = checks

    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        report: Dict[str, Any] = {}
        ok = True
        for chk in self.checks:
            res = chk.run(df)
            report[chk.__class__.__name__] = res
            ok = ok and bool(res.get("ok", True))
        report["ok"] = ok
        report["checksum"] = df_checksum(df)
        return report
