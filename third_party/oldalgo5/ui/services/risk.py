import pandas as pd, numpy as np
def ann_vol(series: pd.Series, ann:int=252) -> float:
    return float(series.std(ddof=0) * (ann**0.5))
def apply_vol_target(returns: pd.Series, target: float=None):
    if not target or target<=0: return returns
    rv = ann_vol(returns); 
    return returns if rv==0 else returns * (float(target)/rv)
def apply_maxdd_stop(equity: pd.Series, dd_limit: float=0.25) -> pd.Series:
    dd = equity/equity.cummax() - 1.0
    hit = dd < -abs(dd_limit)
    if not hit.any(): return equity
    first = dd[hit].index[0]
    out = equity.copy(); out.loc[first:] = equity.loc[first]; return out
