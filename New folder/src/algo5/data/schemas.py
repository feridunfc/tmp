from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence, Dict, Any

OHLCV_REQUIRED = ("Open", "High", "Low", "Close", "Volume")

@dataclass(frozen=True)
class Schema:
    required: Sequence[str] = OHLCV_REQUIRED
    optional: Sequence[str] = ()

DEFAULT_OHLCV_SCHEMA = Schema()

LOWER_TO_PROPER = {
    "open": "Open", "high": "High", "low": "Low",
    "close": "Close", "volume": "Volume",
}

def normalize_column_names(columns: Sequence[str]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    seen = set(columns)
    for c in columns:
        low = str(c).lower()
        if low in LOWER_TO_PROPER and LOWER_TO_PROPER[low] not in seen:
            mapping[c] = LOWER_TO_PROPER[low]
    return mapping
