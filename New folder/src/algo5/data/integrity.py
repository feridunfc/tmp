
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import Dict
import pandas as pd

def df_checksum(df: pd.DataFrame) -> str:
    """Deterministic checksum of a DataFrame (values + index)."""
    # hash_pandas_object is stable across runs (given same pandas version)
    h = pd.util.hash_pandas_object(df, index=True)
    return hashlib.md5(h.values).hexdigest()

@dataclass
class Reproducibility:
    """Simple reproducibility helper.

    - global_seed: base seed to combine with per-strategy hash
    - get_strategy_seed(name): stable seed for a given strategy name
    """
    global_seed: int = 42
    _memo: Dict[str, int] = field(default_factory=dict)

    def get_strategy_seed(self, strategy_name: str) -> int:
        if strategy_name not in self._memo:
            # stable, bounded seed derived from name + global
            seed = (abs(hash(str(strategy_name))) % 100_000) + int(self.global_seed)
            self._memo[strategy_name] = seed
        return self._memo[strategy_name]
