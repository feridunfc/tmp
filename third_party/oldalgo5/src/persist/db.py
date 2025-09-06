from __future__ import annotations
import os, json, time, random
from typing import Dict, Any, Optional

import duckdb
import pandas as pd

DEFAULT_DB = os.environ.get("ALGO2_DB", "results/experiments.duckdb")
SCHEMA_VERSION = 1

DDL = [
    """CREATE TABLE IF NOT EXISTS meta (
        key   VARCHAR,
        value VARCHAR
    );""",
    # DuckDB 1.3.x için GENERATED/IDENTITY kaldırıldı; run_id uygulamada üretilecek
    """CREATE TABLE IF NOT EXISTS runs (
        run_id     BIGINT,
        kind       VARCHAR,     -- 'backtest'|'paper'|'walk'|'hpo'
        strategy   VARCHAR,
        symbol     VARCHAR,
        params     JSON,
        metrics    JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""",
    """CREATE TABLE IF NOT EXISTS equity (
        run_id      BIGINT,
        ts          TIMESTAMP,
        total_value DOUBLE,
        cash        DOUBLE
    );""",
    """CREATE TABLE IF NOT EXISTS orders (
        run_id       BIGINT,
        ts           TIMESTAMP,
        symbol       VARCHAR,
        side         VARCHAR,
        qty          DOUBLE,
        price        DOUBLE,
        status       VARCHAR,
        realized_pnl DOUBLE DEFAULT 0.0
    );"""
]

def _new_run_id() -> int:
    # ms cinsinden zaman + 0-999 rastgele kuyruk: aynı ms'de çakışmayı azaltır
    return int(time.time() * 1000) * 1000 + random.randint(0, 999)

def _conn(db_path: str = DEFAULT_DB):
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    con = duckdb.connect(db_path)
    for ddl in DDL:
        con.execute(ddl)

    # schema_version meta kaydı
    row = con.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    if not row:
        con.execute("INSERT INTO meta VALUES ('schema_version', ?)", [str(SCHEMA_VERSION)])
    return con

def save_run(
    kind: str,
    strategy: str,
    symbol: str,
    *,
    params: Dict[str, Any],
    metrics: Dict[str, Any],
    db_path: str = DEFAULT_DB
) -> int:
    con = _conn(db_path)
    rid = _new_run_id()
    con.execute(
        "INSERT INTO runs(run_id, kind, strategy, symbol, params, metrics) VALUES (?,?,?,?,?,?)",
        [rid, kind, strategy, symbol, json.dumps(params), json.dumps(metrics)],
    )
    con.close()
    return int(rid)

def save_equity(run_id: int, df: pd.DataFrame, db_path: str = DEFAULT_DB) -> None:
    con = _conn(db_path)
    out = df.copy()
    if out.index.name:  # index ts ise index'i kolona al
        out = out.reset_index(names=["ts"])
    elif "ts" not in out.columns:
        # ilk sütun zaman ise ismini ts yapmaya çalış
        first_col = out.columns[0]
        out = out.rename(columns={first_col: "ts"})
    # DuckDB'ye geçici tablo olarak kaydet
    con.register("out", out)
    con.execute(
        "INSERT INTO equity SELECT ?, ts, total_value, cash FROM out",
        [run_id],
    )
    con.unregister("out")
    con.close()

def save_orders(run_id: int, df: pd.DataFrame, db_path: str = DEFAULT_DB) -> None:
    con = _conn(db_path)
    out = df.copy()
    # Beklenen kolonlar: ts, symbol, side, qty, price, status, realized_pnl
    if "realized_pnl" not in out.columns:
        out["realized_pnl"] = 0.0
    con.register("out", out)
    con.execute(
        "INSERT INTO orders SELECT ?, ts, symbol, side, qty, price, status, realized_pnl FROM out",
        [run_id],
    )
    con.unregister("out")
    con.close()

def list_runs(db_path: str = DEFAULT_DB) -> pd.DataFrame:
    con = _conn(db_path)
    df = con.execute("SELECT * FROM runs ORDER BY run_id DESC").df()
    con.close()
    return df

def query_runs(
    strategy: Optional[str] = None,
    symbol: Optional[str] = None,
    db_path: str = DEFAULT_DB
) -> pd.DataFrame:
    con = _conn(db_path)
    if strategy and symbol:
        df = con.execute(
            "SELECT * FROM runs WHERE strategy=? AND symbol=? ORDER BY run_id DESC",
            [strategy, symbol],
        ).df()
    elif strategy:
        df = con.execute(
            "SELECT * FROM runs WHERE strategy=? ORDER BY run_id DESC",
            [strategy],
        ).df()
    elif symbol:
        df = con.execute(
            "SELECT * FROM runs WHERE symbol=? ORDER BY run_id DESC",
            [symbol],
        ).df()
    else:
        df = con.execute("SELECT * FROM runs ORDER BY run_id DESC").df()
    con.close()
    return df
