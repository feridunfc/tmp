from __future__ import annotations

import numpy as np

from algo5.data.integrity import df_checksum, Reproducibility


def test_df_checksum_changes_when_data_changes(demo_df):
    h1 = df_checksum(demo_df)
    demo_df.loc[demo_df.index[0], "Close"] += 1.0
    h2 = df_checksum(demo_df)
    assert h1 != h2


def test_reproducibility_seed_if_available():
    r = Reproducibility(global_seed=123)
    a = np.random.RandomState(r.get_strategy_seed("strat_a")).rand()
    b = np.random.RandomState(r.get_strategy_seed("strat_a")).rand()
    c = np.random.RandomState(r.get_strategy_seed("strat_b")).rand()
    assert a == b
    assert a != c
