import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

from src.signal.overlay import apply_overlays

def _demo_df(n=200):
    now = datetime.now(timezone.utc)
    idx = pd.date_range(now - timedelta(hours=n), periods=n, freq="h", tz="UTC")
    p = 100 + np.cumsum(np.random.randn(n)) * 0.3
    df = pd.DataFrame({"Close": p}, index=idx)
    return df

def test_overlay_shapes_and_meta():
    df = _demo_df(240)
    raw = pd.Series(np.random.choice([-1,0,1], size=len(df)), index=df.index).astype(float)

    net, meta = apply_overlays(
        raw, df,
        use_sentiment=True, sentiment_mode="gate", sentiment_threshold=0.9,
        use_anomaly=True, anomaly_method="zscore", z_win=20, z_thresh=2.5,
    )
    assert len(net) == len(raw)
    assert set(["sentiment_score", "anomaly_pass"]).issubset(set(meta.keys()))
    # gating/anomaly should not increase absolute magnitude
    assert (net.abs() <= raw.abs() + 1e-9).all()
