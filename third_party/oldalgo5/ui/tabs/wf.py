from __future__ import annotations
import streamlit as st
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from ui.common.services import get_active_df, normalize_ohlcv
import plotly.graph_objects as pgo

try:
    from src.core.strategies.registry import list_strategies, get_strategy
except Exception:
    def list_strategies(): return ["ma_crossover"]
    def get_strategy(name: str, **params):
        class _S:
            @staticmethod
            def param_schema():
                return [{"name":"lookback","type":"int","default":20,"min":5,"max":200,"step":1}]
            def prepare(self, df): return df
            def generate_signals(self, df):
                lb = int(params.get("lookback",20))
                ma = df["close"].rolling(lb).mean()
                return (df["close"] > ma).astype(int).replace(0,-1)
        return _S()


# ui/tabs/wf.py (en üstte)
try:
    from sklearn.model_selection import TimeSeriesSplit  # varsa bunu kullan
except Exception:
    # Basit bir yedek TSCV
    class TimeSeriesSplit:
        def __init__(self, n_splits=5, test_size=None):
            self.n_splits = n_splits
            self.test_size = test_size

        def split(self, X):
            n = len(X)
            if n <= 1:
                return
            # test_size verilmemişse eşit böl
            ts = self.test_size or max(1, n // (self.n_splits + 1))
            # ilk train, son n_splits*ts test dilimi için alan bırak
            first_train_end = n - ts * self.n_splits
            if first_train_end <= 1:
                first_train_end = max(1, n // 2)
            for i in range(self.n_splits):
                train_end = first_train_end + i * ts
                test_start = train_end
                test_end = min(n, test_start + ts)
                if test_start >= test_end:
                    break
                yield range(0, train_end), range(test_start, test_end)


def render(ctx):
    st.subheader("🚶 Walk-Forward Analizi")

    with st.form("wf_form"):
        sel = st.selectbox("Strateji", list_strategies(), index=0, key="wf_sel")
        n_splits = st.number_input("Split sayısı", 2, 20, 5, 1, key="wf_splits")
        btn = st.form_submit_button("WF Çalıştır", type="primary", width='stretch')

    if not btn:
        return

    df = normalize_ohlcv(get_active_df())

    proto = get_strategy(sel)
    schema = []
    if hasattr(proto, "param_schema"):
        try: schema = proto.param_schema()
        except Exception: schema = []
    params = {f.get("name"): f.get("default") for f in schema if isinstance(f, dict)}

    curves = []
    tscv = TimeSeriesSplit(n_splits=int(n_splits))
    for fold, (tr, te) in enumerate(tscv.split(df)):
        train_df, test_df = df.iloc[tr], df.iloc[te]
        strat = get_strategy(sel, **params)
        pre_train = strat.prepare(train_df) if hasattr(strat, "prepare") else train_df
        _ = strat.generate_signals(pre_train)

        pre_test = strat.prepare(test_df) if hasattr(strat, "prepare") else test_df
        sig = strat.generate_signals(pre_test)
        rets = pre_test["close"].pct_change().fillna(0.0)
        pos = sig.shift(1).fillna(0.0)
        eq = (1 + rets * pos).cumprod()
        curves.append(eq.rename(f"Fold {fold+1}"))

    if curves:
        fig = pgo.Figure()
        for eq in curves:
            fig.add_trace(pgo.Scatter(x=eq.index, y=eq.values, name=eq.name, mode="lines"))
        st.plotly_chart(fig, width='stretch', key="wf_plot")
