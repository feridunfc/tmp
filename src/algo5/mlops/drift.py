
from __future__ import annotations
import numpy as np
import pandas as pd

def psi(ref: pd.Series, cur: pd.Series, bins: int = 10) -> float:
    r, edges = np.histogram(ref.dropna(), bins=bins, range=(ref.min(), ref.max()))
    c, _ = np.histogram(cur.dropna(), bins=bins, range=(ref.min(), ref.max()))
    r = r / (r.sum() + 1e-12)
    c = c / (c.sum() + 1e-12)
    vals = (c - r) * np.log((c + 1e-12) / (r + 1e-12))
    return float(np.nan_to_num(vals).sum())

def features_psi(ref_df: pd.DataFrame, cur_df: pd.DataFrame, bins: int = 10) -> pd.Series:
    common = sorted(set(ref_df.columns) & set(cur_df.columns))
    return pd.Series({col: psi(ref_df[col], cur_df[col], bins) for col in common})
