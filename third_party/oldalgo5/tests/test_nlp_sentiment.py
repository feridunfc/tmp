import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

from src.nlp.sentiment import compute_sentiment_scores

def _demo_df(n=200):
    now = datetime.now(timezone.utc)
    idx = pd.date_range(now - timedelta(hours=n), periods=n, freq="h", tz="UTC")
    p = 100 + np.cumsum(np.random.randn(n)) * 0.3
    df = pd.DataFrame({"Close": p}, index=idx)
    return df

def test_sentiment_shape_and_range():
    df = _demo_df(240)
    s = compute_sentiment_scores(df)
    assert len(s) == len(df)
    assert s.index.equals(df.index)
    assert (s.values >= -1.0).all() and (s.values <= 1.0).all()
    assert not np.isnan(s.values).any()
