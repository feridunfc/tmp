import pandas as pd
class BaseStrategy:
    @classmethod
    def name(cls) -> str: return cls.__name__
    @classmethod
    def param_schema(cls) -> dict: return {}
    @classmethod
    def generate_signals(cls, df: pd.DataFrame, params: dict) -> pd.Series: raise NotImplementedError
