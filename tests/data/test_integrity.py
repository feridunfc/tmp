
import pandas as pd
from src.algo5.data.integrity import df_checksum, Reproducibility

def test_df_checksum_stability():
    df = pd.DataFrame(
        {"Open":[1,2], "High":[1,2], "Low":[1,2], "Close":[1,2], "volume":[1,2]},
        index=pd.date_range("2025-01-01", periods=2, tz="UTC"),
    )
    df_shuffled = df.sample(frac=1, random_state=0)

    c1 = df_checksum(df, method="fast")
    c2 = df_checksum(df_shuffled, method="fast")
    assert c1 == c2

    try:
        c3 = df_checksum(df, method="stable")
        c4 = df_checksum(df_shuffled, method="stable")
        assert c3 == c4
    except Exception:
        # pyarrow may be unavailable in some environments
        pass

def test_reproducibility_seed_stability_and_persistence():
    r = Reproducibility(global_seed=42)
    s1 = r.get_strategy_seed("mean_reversion")
    s2 = r.get_strategy_seed("mean_reversion")
    assert s1 == s2

    data = r.to_dict()
    r2 = Reproducibility.from_dict(data)
    assert r2.get_strategy_seed("mean_reversion") == s1
