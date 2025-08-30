import numpy as np
import pandas as pd
from algo5.robustness.jitter import jitter_returns
from algo5.robustness.worst_days import remove_best_k_days, remove_worst_k_days
from algo5.robustness.mc import block_bootstrap_returns

def test_jitter_deterministic():
    rets = pd.Series([0.01, -0.02, 0.005, 0.0])
    a = jitter_returns(rets, sigma=0.001, seed=1)
    b = jitter_returns(rets, sigma=0.001, seed=1)
    assert np.allclose(a.values, b.values)

def test_remove_k_days():
    rets = pd.Series([0.10, 0.02, -0.03, 0.04, -0.01])
    best_removed = remove_best_k_days(rets, k=1)
    assert len(best_removed) == len(rets) - 1
    worst_removed = remove_worst_k_days(rets, k=2)
    assert len(worst_removed) == len(rets) - 2

def test_block_bootstrap_len_seed():
    rets = pd.Series([0.01, -0.02, 0.005, 0.01, 0.0, -0.01, 0.003])
    a = block_bootstrap_returns(rets, block=3, n=10, seed=7)
    b = block_bootstrap_returns(rets, block=3, n=10, seed=7)
    assert len(a) == 10 and len(b) == 10
    assert np.allclose(a.values, b.values)
