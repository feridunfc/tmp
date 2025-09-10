
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, List

class FeatureEngine:
    """Hızlı teknik indikatör özellikleri (SMA/RSI/Bollinger).
    API:
        fe = FeatureEngine({'sma':[20,50], 'rsi':14, 'bb':{'period':20,'std':2.0}})
        out = fe.transform(df)
    """
    def __init__(self, config: Dict):
        self.config = config or {}

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        d = df.copy()
        price = d['close'] if 'close' in d.columns else d.get('Close')
        if price is None:
            raise ValueError('FeatureEngine expects close/Close column')

        # SMA
        sma = self.config.get('sma')
        if sma:
            for p in (sma if isinstance(sma, (list,tuple)) else [int(sma)]):
                d[f'sma_{int(p)}'] = price.rolling(int(p)).mean()

        # RSI
        rsi_p = self.config.get('rsi')
        if rsi_p:
            p = int(rsi_p)
            delta = price.diff()
            gain = delta.clip(lower=0).rolling(p).mean()
            loss = (-delta.clip(upper=0)).rolling(p).mean()
            rs = gain / (loss.replace(0, np.nan))
            d['rsi'] = 100 - 100 / (1 + rs)

        # Bollinger
        bb = self.config.get('bb')
        if bb:
            period = int(bb.get('period',20))
            stdv = float(bb.get('std',2.0))
            ma = price.rolling(period).mean()
            std = price.rolling(period).std()
            d['bb_mid'] = ma
            d['bb_up'] = ma + stdv*std
            d['bb_dn'] = ma - stdv*std

        return d
