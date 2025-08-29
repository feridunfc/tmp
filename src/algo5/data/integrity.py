from __future__ import annotations
import hashlib
import numpy as np
import pandas as pd
from dataclasses import dataclass

def df_checksum(df: pd.DataFrame) -> str:
    # stable checksum: values + index
    vals = pd.util.hash_pandas_object(df, index=True).values
    h = hashlib.md5(vals).hexdigest()
    return h

@dataclass
class Reproducibility:
    global_seed: int = 42
    def get_strategy_seed(self, strategy_name: str) -> int:
        # deterministic per-strategy seed
        return (abs(hash(strategy_name)) % 100_000) + self.global_seed

    def seed_all(self, strategy_name: str | None = None):
        import random
        if strategy_name:
            seed = self.get_strategy_seed(strategy_name)
        else:
            seed = self.global_seed
        random.seed(seed)
        try:
            import numpy as np
            np.random.seed(seed)
        except Exception:
            pass
        return seed
