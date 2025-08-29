from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict

import pandas as pd


def df_checksum(df: pd.DataFrame) -> str:
    """Deterministic checksum including index and columns order."""
    # Use pandas hashing to be more stable across platforms
    vals = pd.util.hash_pandas_object(df, index=True).values.tobytes()
    return hashlib.md5(vals).hexdigest()


@dataclass
class Reproducibility:
    global_seed: int = 42
    strategy_seeds: Dict[str, int] | None = None

    def __post_init__(self) -> None:
        if self.strategy_seeds is None:
            self.strategy_seeds = {}

    def get_strategy_seed(self, strategy_name: str) -> int:
        if strategy_name not in self.strategy_seeds:
            # stable per-name seed
            self.strategy_seeds[strategy_name] = (hash(strategy_name) % 100_000) + int(self.global_seed)
        return self.strategy_seeds[strategy_name]
