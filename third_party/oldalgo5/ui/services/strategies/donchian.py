import pandas as pd
from ui.services.strategies.base import BaseStrategy
class Donchian(BaseStrategy):
    @classmethod
    def name(cls): return "Donchian Breakout"
    @classmethod
    def param_schema(cls): return {"channel":{"type":"int","min":5,"max":100,"step":1,"default":20,"label":"Channel"}}
    @classmethod
    def generate_signals(cls, df: pd.DataFrame, params: dict) -> pd.Series:
        px=df["Close"].astype(float); ch=int(params.get("channel",20))
        hh=px.rolling(ch,1).max(); return (px > hh.shift(1)).astype(int)
