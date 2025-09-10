from __future__ import annotations
import pandas as pd, numpy as np
from sklearn.mixture import GaussianMixture

class VolTrendRegime:
    def __init__(self, n_states:int=3, random_state:int=42):
        self.gmm = GaussianMixture(n_components=n_states, covariance_type="full", random_state=random_state)
        self.th_slope = 0.0

    def fit(self, df_feat: pd.DataFrame):
        rv_cols = [c for c in df_feat.columns if c.startswith("rv_")]
        rv = df_feat[rv_cols[0]] if rv_cols else df_feat["close"].pct_change().rolling(20).std().fillna(0.0)
        self.gmm.fit(rv.fillna(0.0).values.reshape(-1,1))
        sma = df_feat.get("sma_50", df_feat["close"].rolling(50).mean())
        self.th_slope = float(sma.diff().median())
        return self

    def predict(self, df_feat: pd.DataFrame)->pd.DataFrame:
        rv_cols = [c for c in df_feat.columns if c.startswith("rv_")]
        rv = df_feat[rv_cols[0]] if rv_cols else df_feat["close"].pct_change().rolling(20).std().fillna(0.0)
        vol_state = self.gmm.predict(rv.fillna(0.0).values.reshape(-1,1))
        sma = df_feat.get("sma_50", df_feat["close"].rolling(50).mean())
        slope = sma.diff()
        trend_up = (slope > self.th_slope).astype(int)
        out = df_feat.copy()
        out["regime_vol_state"] = vol_state
        out["regime_trend_up"] = trend_up.values
        return out
