import hashlib
import pandas as pd
from dataclasses import dataclass


def df_checksum(df: pd.DataFrame) -> str:
    h = pd.util.hash_pandas_object(df, index=True).values
    return hashlib.md5(h).hexdigest()  # type: ignore[arg-type]


@dataclass
class Reproducibility:
    global_seed: int = 42

    def get_strategy_seed(self, strategy_name: str) -> int:
        return (hash(strategy_name) % 100000) + self.global_seed
