
import streamlit as st
from algo5.data.loader import demo_ohlcv
from algo5.features.regime.voltrend import make_regime_features
from algo5.models.regime.labeler import label_by_vol_zscore

def run():
    st.subheader("Regime Features & Labels")
    df = demo_ohlcv(250)
    feats = make_regime_features(df)
    lab = label_by_vol_zscore(feats)
    st.dataframe(df.head(), use_container_width=True)
    st.dataframe(feats.join(lab).head(30), use_container_width=True)
