from __future__ import annotations
import numpy as np
import pandas as pd

def jitter_returns(returns: pd.Series, sigma: float = 0.005, seed: int | None = 42) -> pd.Series:
    """Additive Gaussian jitter on returns (deterministic via seed)."""
    rs = np.random.RandomState(seed) if seed is not None else np.random
    noise = rs.normal(0.0, sigma, size=len(returns))
    out = returns.astype(float).values + noise
    return pd.Series(out, index=returns.index, name=returns.name or "ret_jitter")
