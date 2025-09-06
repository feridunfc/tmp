import numpy as np

from algo5.data.integrity import Reproducibility, df_checksum


def test_df_checksum_changes_when_data_changes(demo_df):
    a = df_checksum(demo_df)
    df2 = demo_df.copy()
    df2.iloc[0, 0] += 1
    b = df_checksum(df2)
    assert a != b


def test_reproducibility_seed_if_available():
    r = Reproducibility(global_seed=123)
    a = np.random.RandomState(r.get_strategy_seed("x")).rand()
    b = np.random.RandomState(r.get_strategy_seed("x")).rand()
    assert a == b
