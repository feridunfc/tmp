from __future__ import annotations
import pandas as pd
import streamlit as st
import plotly.graph_objects as pgo
from typing import Any, Dict, List

from ui.common.services import get_active_df, normalize_ohlcv, ensure_risk_engine, build_risk_ui

try:
    from src.core.backtest.engine import BacktestEngine, FeesConfig
    from src.core.strategies.registry import list_strategies, get_strategy
except Exception:
    BacktestEngine = None
    FeesConfig = None
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

def _g(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict): return obj.get(key, default)
    if hasattr(obj, key): return getattr(obj, key)
    if hasattr(obj, "__dict__"): return obj.__dict__.get(key, default)
    return default

def _schema_to_list(schema: Any) -> List[Dict[str, Any]]:
    if isinstance(schema, list):
        out: List[Dict[str, Any]] = []
        for f in schema:
            if isinstance(f, dict):
                out.append(f)
            else:
                out.append({
                    "name": _g(f, "name", "param"),
                    "type": _g(f, "type", "int"),
                    "default": _g(f, "default", _g(f, "value", None)),
                    "min": _g(f, "min", None),
                    "max": _g(f, "max", None),
                    "step": _g(f, "step", 1),
                    "options": _g(f, "options", None),
                    "log": _g(f, "log", False),
                })
        return out
    return []

def render(ctx):
    st.subheader("⚖️ Karşılaştırma")

    all_strats = list_strategies() or []
    if not all_strats:
        st.error("Kayıtlı strateji yok.")
        return

    with st.form("compare_run_form"):
        chosen = st.multiselect("Stratejiler", all_strats, default=all_strats[:1], key="compare_strats")
        risk_cfg = build_risk_ui(prefix="compare")
        btn_cmp = st.form_submit_button("Karşılaştırmayı Başlat", type="primary", width='stretch')

    if not btn_cmp or not chosen:
        return

    df = normalize_ohlcv(get_active_df())

    fees = None
    if FeesConfig is not None:
        fees = FeesConfig(
            commission_bps=getattr(ctx, "commission_bps", 0.0),
            slippage_bps=getattr(ctx, "slippage_bps", 0.0),
        )

    curves, rows, errors = {}, [], []

    for name in chosen:
        try:
            proto = get_strategy(name)
            schema = []
            if hasattr(proto, "param_schema"):
                try: schema = proto.param_schema()
                except Exception: schema = []
            fields = _schema_to_list(schema)
            params = {str(_g(f, "name")): _g(f, "default") for f in fields if _g(f, "name")}

            strat = get_strategy(name, **params)
            pre = strat.prepare(df) if hasattr(strat, "prepare") else df
            sig = strat.generate_signals(pre)

            if BacktestEngine is not None and FeesConfig is not None:
                eng = BacktestEngine(fees_config=fees, risk_engine=ensure_risk_engine(risk_cfg))
                res = eng.run_backtest(pre, sig)
                eq = res.get("equity")
                metrics = res.get("metrics", {})
            else:
                rets = pre["close"].pct_change().fillna(0.0)
                pos = pd.Series(sig, index=pre.index).shift(1).fillna(0.0)
                eq = (1 + rets * pos).cumprod()
                metrics = {
                    "total_return": float(eq.iloc[-1] - 1.0),
                    "sharpe": float((rets * pos).mean() / ((rets * pos).std() + 1e-12) * (252 ** 0.5)),
                    "max_drawdown": float((eq / eq.cummax() - 1.0).min()),
                }

            curves[name] = eq
            rows.append({
                "Strateji": name,
                "Toplam Getiri %": metrics.get("total_return", 0.0) * 100.0,
                "Sharpe": metrics.get("sharpe", 0.0),
                "MaxDD %": metrics.get("max_drawdown", 0.0) * 100.0,
            })
        except Exception as e:
            errors.append(f"{name}: {e}")

    if errors:
        with st.expander("Hatalar"):
            for msg in errors:
                st.error(msg)

    if rows:
        cmp_df = pd.DataFrame(rows)
        sort_col = st.selectbox("Sırala", list(cmp_df.columns), index=2, key="compare_sort_col")
        ascending = st.checkbox("Artan sırala", value=False, key="compare_sort_dir")
        st.dataframe(cmp_df.sort_values(sort_col, ascending=ascending), width='stretch', height=350)

        fig = pgo.Figure()
        for n, eq in curves.items():
            fig.add_trace(pgo.Scatter(x=eq.index, y=eq.values, name=n, mode="lines"))
        fig.update_layout(xaxis_title="Zaman", yaxis_title="Equity", legend_title="Stratejiler")
        st.plotly_chart(fig, width='stretch', key="compare_equity_plot")
