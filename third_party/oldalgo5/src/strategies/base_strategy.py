from dataclasses import dataclass
from typing import Any, List

@dataclass
class StrategyParameters:
    params: Any = None

class BaseStrategy:
    name: str = "BaseStrategy"
    family: str = "conventional"

    @staticmethod
    def param_schema() -> List[dict]:
        return []

    @staticmethod
    def prepare(df, **_):
        return df

    @staticmethod
    def generate_signals(df, **_):
        raise NotImplementedError
