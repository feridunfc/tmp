import pandas as pd
import numpy as np
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "results" / "experiments.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def _ensure_datetime_index(n=600):
    end = pd.Timestamp.today().normalize()
    return pd.date_range(end=end, periods=n, freq="B")

def load_data(symbols="AAPL", interval="1d", start=None, end=None):
    rng = np.random.default_rng(7)
    idx = _ensure_datetime_index(600)
    dfs = []
    for sym in [s.strip() for s in str(symbols).split(",") if s.strip()]:
        ret = rng.normal(0.0003, 0.01, len(idx))
        price = 100 * (1 + pd.Series(ret, index=idx)).cumprod()
        high = price * (1 + rng.uniform(0.0, 0.01, len(idx)))
        low  = price * (1 - rng.uniform(0.0, 0.01, len(idx)))
        openp = price.shift(1).fillna(price.iloc[0])
        vol = rng.integers(2e5, 8e5, len(idx))
        df = pd.DataFrame({"Open": openp, "High": high, "Low": low, "Close": price, "Volume": vol}, index=idx)
        df["Symbol"] = sym
        dfs.append(df)
    out = pd.concat(dfs, axis=0)
    out.index.name = "Date"
    if start is not None:
        out = out[out.index >= pd.to_datetime(start)]
    if end is not None:
        out = out[out.index <= pd.to_datetime(end)]
    out = out.sort_index()
    return out

def validate_data(df: pd.DataFrame):
    req = {"Open","High","Low","Close","Volume","Symbol"}
    missing = req - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("Index must be DatetimeIndex")
    return True

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for sym, g in df.groupby("Symbol", group_keys=False):
        g = g.sort_index().copy()
        px = g["Close"].astype(float)
        g["ret"] = px.pct_change().fillna(0.0)
        g["rsi14"] = _rsi(px, 14)
        parts.append(g)
    return pd.concat(parts, axis=0)

def _rsi(px: pd.Series, window=14) -> pd.Series:
    delta = px.diff()
    up = delta.clip(lower=0).rolling(window, min_periods=window).mean()
    down = -delta.clip(upper=0).rolling(window, min_periods=window).mean()
    rs = (up / (down.replace({0: np.nan}))).fillna(0.0)
    return 100 - 100/(1+rs)

def _positions_from_signals(sig: pd.Series) -> pd.Series:
    return sig.shift(1).fillna(0).clip(-1, 1)  # enter next bar

def _max_drawdown(eq: pd.Series) -> float:
    peak = eq.cummax()
    dd = (eq/peak - 1.0).min()
    return float(abs(dd))

def run_backtest_with_signals(df: pd.DataFrame, signals: pd.Series, commission=0.001, slippage=0.0005):
    px = df["Close"].astype(float)
    sig = signals.astype(int).reindex(px.index).fillna(0)
    pos = _positions_from_signals(sig)
    ret = px.pct_change().fillna(0.0)
    trades = pos.diff().abs().fillna(pos.abs())
    costs = trades * (commission + slippage)
    strat_ret = pos * ret - costs
    equity = (1 + strat_ret).cumprod()
    ann = 252
    mu = strat_ret.mean() * ann
    sd = strat_ret.std(ddof=0) * np.sqrt(ann)
    sharpe = float(mu / sd) if sd > 0 else 0.0
    metrics = {
        "AnnReturn": float(mu),
        "Vol": float(sd),
        "Sharpe": float(sharpe),
        "MaxDD": float(_max_drawdown(equity)),
        "CAGR": float((equity.iloc[-1] ** (ann/len(equity)) - 1) if len(equity)>0 else 0.0),
        "FinalEquity": float(equity.iloc[-1]),
        "Bars": int(len(equity)),
    }
    return equity, pos, metrics

def aggregate_results(per_symbol):
    import pandas as pd
    rows = []
    for sym, res in per_symbol.items():
        m = res["metrics"].copy()
        m["Symbol"] = sym
        rows.append(m)
    return pd.DataFrame(rows).set_index("Symbol")

def save_run_to_db(run_id, timestamp, strategy, params: dict, symbols: str, metrics_df):
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            timestamp TEXT,
            strategy TEXT,
            params_json TEXT,
            symbols TEXT,
            sharpe REAL,
            cagr REAL,
            maxdd REAL,
            annret REAL,
            n_symbols INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS metrics_per_symbol (
            run_id TEXT,
            symbol TEXT,
            sharpe REAL,
            cagr REAL,
            maxdd REAL,
            annret REAL,
            final_equity REAL,
            bars INTEGER
        )
    """)
    avg = {
        "sharpe": float(metrics_df["Sharpe"].mean()),
        "cagr": float(metrics_df["CAGR"].mean()),
        "maxdd": float(metrics_df["MaxDD"].mean()),
        "annret": float(metrics_df["AnnReturn"].mean()),
    }
    cur.execute(
        "INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?,?,?,?,?,?)",
        (run_id, timestamp, strategy, json.dumps(params), symbols,
         avg["sharpe"], avg["cagr"], avg["maxdd"], avg["annret"], int(len(metrics_df)))
    )
    for sym, row in metrics_df.iterrows():
        cur.execute(
            "INSERT INTO metrics_per_symbol VALUES (?,?,?,?,?,?,?,?)",
            (run_id, sym, float(row["Sharpe"]), float(row["CAGR"]),
             float(row["MaxDD"]), float(row["AnnReturn"]), float(row["FinalEquity"]), int(row["Bars"]))
        )
    conn.commit()
    conn.close()

def query_runs(limit=50, strategy=None):
    conn = sqlite3.connect(DB_PATH)
    q = "SELECT run_id, timestamp, strategy, params_json, symbols, sharpe, cagr, maxdd, annret, n_symbols FROM runs"
    if strategy:
        q += " WHERE strategy=? ORDER BY timestamp DESC LIMIT ?"
        rows = pd.read_sql_query(q, conn, params=(strategy, limit))
    else:
        q += " ORDER BY timestamp DESC LIMIT ?"
        rows = pd.read_sql_query(q, conn, params=(limit,))
    conn.close()
    return rows

def robustness_mc(equity, n=200, shock_std=0.01, seed=123):
    import numpy as np
    import pandas as pd
    eq = pd.Series(equity).astype(float)
    rets = eq.pct_change().fillna(0.0).to_numpy()
    rng = np.random.default_rng(seed)
    finals = []
    for _ in range(int(n)):
        noise = rng.normal(0.0, shock_std, size=rets.shape[0])
        pert_rets = rets + noise
        path = (1.0 + pd.Series(pert_rets)).cumprod()
        finals.append(float(path.iloc[-1]))
    return finals
