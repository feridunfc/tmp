# ui/tabs/data.py
import streamlit as st
import pandas as pd

from algo5.data.quality.monitor import DataQualityMonitor
from algo5.data.feature_store.store import FeatureStore

# demo_ohlcv varsa kullan, yoksa deterministik fallback üret
try:
    from algo5.data.loader import demo_ohlcv  # mevcutsa buradan gelir
except Exception:
    import numpy as np

    def demo_ohlcv(periods: int = 120, start: str = "2024-01-01") -> pd.DataFrame:
        idx = pd.date_range(start, periods=periods, freq="D")
        base = 100 + np.arange(periods, dtype=float)
        return pd.DataFrame(
            {
                "Open": base,
                "High": base + 1,
                "Low":  base - 1,
                "Close": base,
                "Volume": 1000 + np.arange(periods, dtype=int),
            },
            index=idx,
        )



import streamlit as st
import pandas as pd
import numpy as np

from src.algo5.data.validate import validate_ohlcv
from algo5.data.quality.monitor import DataQualityMonitor
from algo5.data.feature_store.store import FeatureStore
from algo5.data.loader import demo_ohlcv   # varsa; yoksa kendi df'ini kullan


def _read_upload(file) -> pd.DataFrame:
    name = file.name.lower()
    if name.endswith(".parquet"):
        return pd.read_parquet(file)
    return pd.read_csv(file)


def _demo_df(n=500) -> pd.DataFrame:
    rng = pd.date_range(end=pd.Timestamp.today().normalize(), periods=n, freq="D")
    base = 100 + np.cumsum(np.random.randn(n))
    return pd.DataFrame(
        {
            "Open": base * (1 - 0.002),
            "High": base * (1 + 0.01),
            "Low":  base * (1 - 0.01),
            "Close": base,
            "Volume": np.random.randint(1_000, 5_000, n),
        },
        index=rng,
    )


def run():
    st.header("Data Quality & Cache")

    # Veri seçimi / demo fallback
    df: pd.DataFrame
    if "data" in st.session_state and isinstance(st.session_state["data"], pd.DataFrame):
        df = st.session_state["data"]
        st.caption("Session verisi bulundu.")
    else:
        df = demo_ohlcv(periods=120)
        st.caption("Session verisi bulunamadı; demo veri kullanılıyor.")

    # Quality
    if st.button("Check Quality"):
        report = DataQualityMonitor().run(df)
        st.json(report)

    # Cache
    st.divider()
    st.subheader("Feature Store Cache")
    col1, col2 = st.columns(2)
    with col1:
        ns = st.text_input("Namespace", value="raw")
    with col2:
        name = st.text_input("Key / Name", value="demo_ohlcv")

    if st.button("Build Cache"):
        try:
            store = FeatureStore(namespace=ns)         # <--- artık destekli
            key = name                                 # istersen "ns/name" biçimi de verebilirsin
            path = store.save(key, df, overwrite=True)
            st.success(f"Cached: {path}")
        except Exception as e:
            st.error(f"Cache error: {e!r}")
