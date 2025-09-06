from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

def load_demo_feed(n_hours: int = 72) -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    idx = pd.date_range(end=now, periods=n_hours, freq="H", tz="UTC")
    pos = ["gain", "bull", "up", "beat", "profit"]
    neg = ["loss", "bear", "down", "miss", "risk"]
    texts = []
    for i in range(len(idx)):
        if np.random.rand() > 0.5:
            w = np.random.choice(pos)
        else:
            w = np.random.choice(neg)
        texts.append(f"Market {w} on session {i}")
    return pd.DataFrame({"time": idx, "text": texts})
