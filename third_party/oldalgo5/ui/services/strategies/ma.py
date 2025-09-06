import pandas as pd
from ui.services.strategies.base import BaseStrategy
class MA(BaseStrategy):
    @classmethod
    def name(cls): return "MA Crossover"
    @classmethod
    def param_schema(cls): return {"fast":{"type":"int","min":2,"max":200,"step":1,"default":10,"label":"MA Fast"}, "slow":{"type":"int","min":5,"max":400,"step":1,"default":30,"label":"MA Slow"}}
    @classmethod
    def generate_signals(cls, df: pd.DataFrame, params: dict) -> pd.Series:
        px = df["Close"].astype(float); f=int(params.get("fast",10)); s=int(params.get("slow",30))
        return (px.rolling(f,1).mean() > px.rolling(s,1).mean()).astype(int)
