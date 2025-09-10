from __future__ import annotations
import pandas as pd
import numpy as np
import streamlit as st

def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["open","high","low","close","volume"])
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    # Map Close/close both ways to avoid KeyError
    if "close" not in out.columns and "Close" in out.columns:
        out["close"] = out["Close"]
    if "Close" not in out.columns and "close" in out.columns:
        out["Close"] = out["close"]
    if "open" not in out.columns:
        out["open"] = out.get("Open", out["close"])
    if "high" not in out.columns:
        out["high"] = out.get("High", out["close"])
    if "low" not in out.columns:
        out["low"] = out.get("Low", out["close"])
    if "volume" not in out.columns:
        out["volume"] = out.get("Volume", 0.0)
    if not isinstance(out.index, pd.DatetimeIndex):
        try:
            out.index = pd.to_datetime(out.index, utc=True)
        except Exception:
            out.index = pd.date_range("2024-01-01", periods=len(out), freq="D", tz="UTC")
    out = out[["open","high","low","close","volume"]].sort_index()
    return out

def _synth_df(n: int = 400) -> pd.DataFrame:
    idx = pd.date_range("2023-01-01", periods=n, freq="D", tz="UTC")
    rng = np.random.default_rng(42)
    steps = rng.normal(0, 0.01, size=n).cumsum()
    base = 100 + steps
    df = pd.DataFrame({
        "open": pd.Series(base).shift(1).fillna(base[0]).values,
        "high": base * (1 + np.abs(rng.normal(0, 0.002, size=n))),
        "low": base * (1 - np.abs(rng.normal(0, 0.002, size=n))),
        "close": base,
        "volume": 1000 + rng.normal(0, 50, size=n)
    }, index=idx)
    return normalize_ohlcv(df)

_UP = "uploaded_df_cache_v1"

def set_uploaded_df(df: pd.DataFrame):
    st.session_state[_UP] = normalize_ohlcv(df)

def get_active_df() -> pd.DataFrame:
    df = st.session_state.get(_UP)
    if isinstance(df, pd.DataFrame) and not df.empty:
        return normalize_ohlcv(df)
    return _synth_df()

def ensure_risk_engine(cfg: dict | None):
    try:
        from src.core.risk.engine import RiskEngine, RiskConfig
        rc = RiskConfig(**(cfg or {}))
        return RiskEngine(rc)
    except Exception:
        return None

def build_risk_ui(prefix: str = "risk") -> dict:
    with st.expander("Risk Ayarları", expanded=False):
        max_pos = st.number_input("Maks. Pozisyon (|w| toplam)", 0.0, 1.0, 1.0, 0.05, key=f"{prefix}_maxpos")
        vol_tgt = st.number_input("Yıllık Vol Target", 0.0, 1.0, 0.2, 0.01, key=f"{prefix}_voltgt")
    return {"max_gross_exposure": max_pos, "vol_target": vol_tgt}
