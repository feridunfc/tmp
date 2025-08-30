
from __future__ import annotations
import numpy as np
import pandas as pd

def _kmeans(X: np.ndarray, k: int = 3, iters: int = 50, seed: int = 42) -> np.ndarray:
    # minimal 1D k-means
    rng = np.random.default_rng(seed)
    X1 = X.reshape(-1, 1).astype(float)
    centers = np.quantile(X1, np.linspace(0, 1, k+2)[1:-1])
    for _ in range(iters):
        d = np.abs(X1 - centers.reshape(1, -1))
        lab = d.argmin(axis=1)
        for j in range(k):
            sel = X1[lab == j]
            if sel.size:
                centers[j] = float(sel.mean())
    return lab

def label_by_vol_zscore(feats: pd.DataFrame, n_states: int = 3, seed: int = 42) -> pd.Series:
    x = feats["zvol"].to_numpy()
    lab = _kmeans(x, k=n_states, seed=seed)
    means = []
    for i in range(n_states):
        m = x[lab == i].mean() if (lab == i).any() else 999.0
        means.append(m)
    order = np.argsort(means)
    remap = {int(order[i]): i for i in range(n_states)}
    y = np.vectorize(lambda v: remap[int(v)])(lab)
    return pd.Series(y, index=feats.index, name="regime")
