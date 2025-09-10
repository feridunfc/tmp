import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

from src.anomaly.zscore_detector import anomaly_mask_zscore

def _demo_df_with_spike(n=200, spike_at=-1, spike_size=0.5):
    now = datetime.now(timezone.utc)
    idx = pd.date_range(now - timedelta(hours=n), periods=n, freq="h", tz="UTC")
    p = 100 + np.cumsum(np.random.randn(n)) * 0.2
    if spike_at < 0:
        spike_at = n + spike_at
    p[spike_at] *= (1.0 + spike_size)  # big jump
    return pd.DataFrame({"Close": p}, index=idx)

def test_zscore_detects_spike():
    df = _demo_df_with_spike()
    mask = anomaly_mask_zscore(df, window=20, threshold=2.5)
    # At least one anomaly detected (False)
    assert (~mask).any()
