
import pytest
import numpy as np

mod = pytest.importorskip("algo5.data.integrity")

def test_df_checksum_changes_when_data_changes(demo_df):
    cs1 = mod.df_checksum(demo_df)
    df2 = demo_df.copy()
    df2.iloc[0, df2.columns.get_loc("Close")] += 1.23
    cs2 = mod.df_checksum(df2)
    assert cs1 != cs2

def test_reproducibility_seed_if_available():
    # optional: class may not exist yet
    if not hasattr(mod, "Reproducibility"):
        pytest.skip("Reproducibility class not present; skipping.")
    r = mod.Reproducibility(global_seed=123)
    a = np.random.RandomState(r.get_strategy_seed("strat_a")).rand()
    b = np.random.RandomState(r.get_strategy_seed("strat_a")).rand()
    assert a == b  # same seed → same draw
