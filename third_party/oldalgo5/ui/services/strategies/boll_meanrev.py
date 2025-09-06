import pandas as pd
from ui.services.strategies.base import BaseStrategy
from ui.services import features as F
class BollingerMR(BaseStrategy):
    @classmethod
    def name(cls): return "Bollinger Mean-Reversion"
    @classmethod
    def param_schema(cls): return {"window":{"type":"int","min":5,"max":100,"step":1,"default":20,"label":"Window"},"nstd":{"type":"float","min":1.0,"max":4.0,"step":0.1,"default":2.0,"label":"Std Mult"}}
    @classmethod
    def generate_signals(cls, df: pd.DataFrame, params: dict) -> pd.Series:
        px=df["Close"].astype(float); w=int(params.get("window",20)); n=float(params.get("nstd",2.0))
        mid, up, lo = F.bollinger(px, w, n); sig = (px < lo).astype(int); sig[px>up]=0; return sig
