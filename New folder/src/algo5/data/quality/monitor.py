
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

REQUIRED = ("Open","High","Low","Close","Volume")

@dataclass
class SchemaCheck:
    required: tuple = REQUIRED
    def run(self, df: pd.DataFrame):
        missing = set(self.required) - set(df.columns)
        return {"ok": len(missing) == 0, "missing": missing}

class DataQualityMonitor:
    def __init__(self, checks=None):
        self.checks = checks or (SchemaCheck(),)
    def run(self, df: pd.DataFrame) -> dict:
        return {type(c).__name__: c.run(df) for c in self.checks}
