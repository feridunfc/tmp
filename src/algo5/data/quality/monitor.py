from dataclasses import dataclass

import pandas as pd

from ..integrity import df_checksum
from ..validate import validate_ohlcv


@dataclass
class SchemaCheck:
    def run(self, df: pd.DataFrame):
        _, rep = validate_ohlcv(df, raise_errors=False)
        return rep


class DataQualityMonitor:
    def __init__(self):
        self.checks = (SchemaCheck(),)

    def run(self, df: pd.DataFrame) -> dict:
        out = {}
        ok = True
        for chk in self.checks:
            r = chk.run(df)
            ok = ok and r.get("ok", True)
            out[chk.__class__.__name__] = r
        out["ok"] = ok
        out["checksum"] = df_checksum(df)
        return out
