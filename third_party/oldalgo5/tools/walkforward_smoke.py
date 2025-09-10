from __future__ import annotations

import os, sys
from pathlib import Path
import numpy as np
import pandas as pd

# --- PYTHONPATH guard ---
ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "src").resolve()
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
os.environ["PYTHONPATH"] = str(SRC)

from strategies.registry import bootstrap, get_registry, get_strategy


def toy_df(n: int = 600, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2019-01-01", periods=n, freq="D")
    drift = 0.02 / 252  # minik pozitif drift
    noise = rng.standard_normal(n) * 0.9
    close = 100 + np.cumsum(drift + noise)
    open_ = close + rng.normal(0, 0.1, n)
    high = np.maximum(open_, close) + np.abs(rng.normal(0, 0.5, n))
    low  = np.minimum(open_, close) - np.abs(rng.normal(0, 0.5, n))
    vol  = 1000 + rng.integers(0, 200, n)
    df = pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": vol}, index=idx)
    return df


def defaults_from_schema(schema) -> dict:
    """
    Field listesi (Field ya da dict) → {name: default}.
    'None' default’ları eler (WF’de NoneType hatasını önler).
    """
    out = {}
    for f in schema or []:
        if hasattr(f, "name"):  # Field dataclass
            default = getattr(f, "default", None)
            if default is not None:
                out[f.name] = default
        elif isinstance(f, dict):
            name = f.get("name")
            default = f.get("default", None)
            if name and default is not None:
                out[name] = default
    return out


def wf(df: pd.DataFrame, strat, params: dict, splits: int = 4):
    """
    Basit WF smoke: full-prep + full-sinyal → her fold’ta 1-bar delay ile PnL.
    Amaç: kırılmıyor mu? Sinyal uzunluğu, NaN/inf vs. kontrol.
    """
    # Hazırlık
    d_all = strat.prepare(df.copy(), **params) if hasattr(strat, "prepare") else df
    sig = strat.generate_signals(d_all, **params)
    sig = pd.Series(sig, index=d_all.index, name="signal") if not isinstance(sig, pd.Series) else sig

    L = len(df)
    fold = L // (splits + 1)
    rets = df["Close"].pct_change().fillna(0.0)

    out = []
    for i in range(splits):
        t0 = (i + 1) * fold
        t1 = (i + 2) * fold if i < splits - 1 else L
        idx = df.index[t0:t1]
        s = sig.loc[idx].shift(1).fillna(0.0)
        pnl = (s * rets.loc[idx]).fillna(0.0)

        std = float(pnl.std())
        mean = float(pnl.mean())
        sharpe = float(np.sqrt(252) * (mean / (std + 1e-12)))
        trades = int((s.diff().abs() > 0).sum())
        out.append((i + 1, sharpe, trades))
    return out


if __name__ == "__main__":
    bootstrap("both")
    REG, ORDER = get_registry()
    df = toy_df()

    # Kısa smoke için rule-based’leri çalıştıralım (ML model/yük şartı olabiliyor)
    keys = [k for k, _ in ORDER if REG[k].get("family") == "rule_based"]

    for key in keys:
        strat = get_strategy(key)
        base_params = defaults_from_schema(REG[key].get("schema"))
        res = wf(df, strat, base_params, splits=4)
        print(f"\n{key} WF:")
        for fold, sh, tr in res:
            print(f"  fold {fold}: sharpe={sh:.2f} trades={tr}")
