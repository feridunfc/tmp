import pandas as pd
from ui.services.strategies.base import BaseStrategy
from ui.services import features as F
class RSI_MR(BaseStrategy):
    @classmethod
    def name(cls): return "RSI Mean-Reversion"
    @classmethod
    def param_schema(cls): return {"rsi_window":{"type":"int","min":3,"max":50,"step":1,"default":14,"label":"RSI Window"},"lower":{"type":"int","min":1,"max":49,"step":1,"default":30,"label":"RSI Lower"},"upper":{"type":"int","min":51,"max":99,"step":1,"default":70,"label":"RSI Upper"}}
    @classmethod
    def generate_signals(cls, df: pd.DataFrame, params: dict) -> pd.Series:
        px = df["Close"].astype(float); w=int(params.get("rsi_window",14)); lo=int(params.get("lower",30)); up=int(params.get("upper",70))
        r = F.rsi(px, w); sig = (r < lo).astype(int); sig[r > up] = 0; return sig
