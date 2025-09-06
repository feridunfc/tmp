import pandas as pd, numpy as np
def rsi(series: pd.Series, window: int=14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0).rolling(window, min_periods=window).mean()
    down = -delta.clip(upper=0).rolling(window, min_periods=window).mean()
    rs = up / down.replace({0: np.nan})
    return (100 - 100/(1+rs)).fillna(50)
def bollinger(series: pd.Series, window:int=20, nstd:float=2.0):
    m = series.rolling(window, min_periods=1).mean()
    s = series.rolling(window, min_periods=1).std(ddof=0)
    return m, m+nstd*s, m-nstd*s
def make_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    px = df["Close"].astype(float)
    feat = pd.DataFrame(index=df.index)
    feat["ret_1"] = px.pct_change().fillna(0.0)
    feat["mom_5"] = (px/px.shift(5)-1).fillna(0.0)
    feat["mom_20"] = (px/px.shift(20)-1).fillna(0.0)
    feat["vol_20"] = px.pct_change().rolling(20, min_periods=5).std(ddof=0).fillna(0.0)
    feat["rsi_14"] = rsi(px, 14)
    m, u, l = bollinger(px, 20, 2.0)
    feat["boll_mid"] = m; feat["boll_up"] = u; feat["boll_lo"] = l
    return (
        feat.replace([np.inf, -np.inf], np.nan)
        .ffill()
        .bfill()
    )


def make_labels(df: pd.DataFrame, horizon:int=1, threshold:float=0.0) -> pd.Series:
    px = df["Close"].astype(float)
    fwd = px.shift(-horizon)/px - 1.0
    return (fwd > threshold).astype(int)
