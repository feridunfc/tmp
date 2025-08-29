import numpy as np
import pandas as pd
from algo5.data.integrity import df_checksum, Reproducibility

def test_df_checksum_stable(demo_df):
    a = df_checksum(demo_df)
    b = df_checksum(demo_df.copy())
    assert a == b

def test_reproducibility_strategy_seed():
    r = Reproducibility(global_seed=123)
    s1 = r.get_strategy_seed("alpha")
    s2 = r.get_strategy_seed("alpha")
    assert s1 == s2
    rng = np.random.RandomState(s1)
    assert 0.0 <= rng.rand() <= 1.0
