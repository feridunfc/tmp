from __future__ import annotations
import pandas as pd

def sharpe(ret: pd.Series, rf: float=0.0, ann:int=252)->float:
    if len(ret)==0: return 0.0
    ex = ret - rf/ann
    sd = ex.std(ddof=0)
    if sd==0 or pd.isna(sd): return 0.0
    return float(ex.mean()/sd * (ann**0.5))

def maxdd(eq: pd.Series)->float:
    if len(eq)==0: return 0.0
    roll = eq.cummax()
    dd = (eq/roll - 1.0).min()
    return float(dd)

def calmar(ret: pd.Series, eq: pd.Series, ann:int=252)->float:
    if len(ret)==0: return 0.0
    ar = (1+ret).prod()**(ann/len(ret)) - 1.0
    mdd = abs(maxdd(eq))
    return float(0.0 if mdd==0 else ar/mdd)
