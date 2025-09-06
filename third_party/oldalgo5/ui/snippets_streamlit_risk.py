import streamlit as st
from src.core.risk.config import RiskConfig
from src.core.risk.engine import RiskEngine

def render_risk_panel(key: str = "risk") -> RiskEngine | None:
    with st.expander("⚠️ Risk Ayarları", expanded=False):
        use_vol = st.checkbox("Hedef Volatilite (vol-target)", value=True, key=f"{key}_use_vol")
        ann_vol = st.number_input("Yıllık Hedef Vol (örn. 0.15)", value=0.15, step=0.01, format="%.2f", key=f"{key}_ann_vol")
        lookback = st.number_input("Volatilite Lookback (bar)", value=20, step=1, key=f"{key}_lookback")
        maxw = st.number_input("Maks Pozisyon Ağırlığı", value=1.0, step=0.1, key=f"{key}_maxw")

        use_stops = st.checkbox("SL/TP Kullan", value=True, key=f"{key}_use_stops")
        sl = st.number_input("Stop-Loss (%)", value=5.0, step=0.5, key=f"{key}_sl")
        tp = st.number_input("Take-Profit (%)", value=10.0, step=0.5, key=f"{key}_tp")

        use_ks = st.checkbox("Equity Kill-Switch", value=True, key=f"{key}_use_ks")
        mdd = st.number_input("Max Drawdown (%)", value=20.0, step=1.0, key=f"{key}_mdd")

        cfg = RiskConfig(
            use_vol_target=use_vol,
            ann_vol_target=float(ann_vol),
            vol_lookback=int(lookback),
            max_pos_weight=float(maxw),
            use_stops=use_stops,
            stop_loss_pct=float(sl) / 100.0,
            take_profit_pct=float(tp) / 100.0,
            use_kill_switch=use_ks,
            max_drawdown_pct=float(mdd) / 100.0,
        )
        st.caption("Not: Çoklu varlık / portföy kısıtları sonraki sürümde.")
        return RiskEngine(cfg)
