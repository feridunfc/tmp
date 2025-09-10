from __future__ import annotations
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from ..data.validator import DataValidator
from ..data.normalizer import normalize_ohlcv
from ..features.engine import FeatureEngine
from ..regime.detector import VolTrendRegime
from ..core.contracts import STRATEGY_REGISTRY
from ..backtest.engine import BacktestEngine, Fees
from ..backtest.metrics import sharpe, maxdd, calmar

def run_pipeline(df_raw: pd.DataFrame, strategy_name: str,
                 feature_spec: list[tuple[str,dict]] | None = None,
                 wf_splits: int = 5) -> tuple[pd.DataFrame, dict]:
    df = normalize_ohlcv(df_raw)
    rep = DataValidator(strict=True).validate_ohlcv(df, "SYMBOL")
    if not rep.is_valid:
        raise ValueError(f"Data problems: {rep.issues}")

    fe = FeatureEngine()
    feats = feature_spec or [("sma", {"windows":[10,30]}), ("rv", {"window":20})]
    df_feat = fe.build(df, feats)
    reg = VolTrendRegime().fit(df_feat)
    df_feat = reg.predict(df_feat)

    tscv = TimeSeriesSplit(n_splits=wf_splits)
    strat_cls = STRATEGY_REGISTRY[strategy_name]
    parts = []
    for tr, te in tscv.split(df_feat):
        train = df_feat.iloc[tr].copy()
        test  = df_feat.iloc[te].copy()
        train["y"] = (train["close"].pct_change().shift(-1) > 0).astype(int)
        test["y"]  = (test["close"].pct_change().shift(-1) > 0).astype(int)
        strat = strat_cls()
        trn = strat.prepare(train); tst = strat.prepare(test)
        if hasattr(strat, "fit"):
            strat.fit(trn, trn["y"])
            tst["proba"] = strat.proba(tst)
        sig = strat.generate_signals(tst)
        out = BacktestEngine(fees=Fees(1.0,2.0), delay=1).run(tst, sig)
        parts.append(out["returns"])

    returns = pd.concat(parts).sort_index()
    equity = (1 + returns).cumprod()
    report = {
        "total_return": float(equity.iloc[-1] - 1.0) if len(equity) else 0.0,
        "sharpe": float(sharpe(returns)),
        "max_drawdown": float(maxdd(equity)),
        "calmar": float(calmar(returns, equity)),
    }
    return pd.DataFrame({"returns": returns, "equity": equity}), report
