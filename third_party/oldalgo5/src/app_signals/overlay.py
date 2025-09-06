from __future__ import annotations
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd

from nlp.sentiment import compute_sentiment_scores
from anomaly.zscore_detector import anomaly_mask_zscore


def apply_overlays(
    raw_signals: pd.Series,
    df: pd.DataFrame,
    *,
    # sentiment
    use_sentiment: bool = False,
    sentiment_mode: str = "gate",          # "gate" | "weight"
    sentiment_threshold: float = 0.5,      # gate: |s| >= thr → geçir
    # anomaly
    use_anomaly: bool = False,
    anomaly_method: str = "zscore",        # şimdilik tek
    z_win: int = 20,
    z_thresh: float = 3.0,
) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Ham sinyale ([-1,0,1] gibi) overlay uygular:
      - Sentiment (gate/weight)
      - Anomali filtresi (zscore)

    Dönüş:
      net_signals (Series), meta (Dict[str,Any])
    """
    if not isinstance(raw_signals, pd.Series):
        raise TypeError("apply_overlays: raw_signals must be pd.Series")
    if df is None or df.empty:
        raise ValueError("apply_overlays: df empty")

    # indeks hizalama
    net = raw_signals.reindex(df.index).fillna(0.0).astype(float)
    meta: Dict[str, Any] = {}

    # --- Sentiment overlay
    if use_sentiment:
        s = compute_sentiment_scores(df).reindex(df.index).fillna(0.0)
        meta["sentiment_score"] = s

        if sentiment_mode.lower() == "gate":
            gate = s.abs() >= float(sentiment_threshold)
            net = net.where(gate, 0.0)
            meta["sentiment_gate"] = gate
        else:  # weight mode
            # |s| / threshold oranı (0..1), threshold=0 korunur
            thr = max(float(sentiment_threshold), 1e-9)
            w = (s.abs() / thr).clip(0.0, 1.0)
            net = net * w
            meta["sentiment_weight"] = w

    # --- Anomaly overlay
    if use_anomaly:
        if anomaly_method.lower() == "zscore":
            mask = anomaly_mask_zscore(df, window=int(z_win), threshold=float(z_thresh))
            meta["anomaly_mask"] = mask
            pass_mask = ~mask  # True = geçer
            meta["anomaly_pass"] = pass_mask
            net = net.where(pass_mask, 0.0)
        else:
            raise ValueError(f"apply_overlays: unsupported anomaly_method '{anomaly_method}'")

    return net, meta
