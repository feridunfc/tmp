

import os, json, duckdb
import pandas as pd
import datetime as dt

# önce
# DB_PATH = os.getenv("ALGO2_DB", "db/algo2.duckdb")

# sonra (geriye dönük uyumlu)
DB_PATH = (os.getenv("APP_DB")
           or os.getenv("ALGO2_DB")
           or "db/app.duckdb")


def _ensure_db_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def _conn():
    _ensure_db_dir()
    return duckdb.connect(DB_PATH)

def init():
    con = _conn()
    con.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id BIGINT PRIMARY KEY,
            ts TIMESTAMP,
            symbol VARCHAR,
            strategy VARCHAR,
            params JSON,
            fees JSON,
            metrics JSON
        );
    """)
    con.close()

def save_run(symbol: str, strategy: str, params: dict, fees: dict, metrics: dict) -> int:
    init()
    con = _conn()
    rid = int(dt.datetime.now().timestamp() * 1e6)
    con.execute(
        "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            rid,
            dt.datetime.now(),
            symbol,
            strategy,
            json.dumps(params),
            json.dumps(fees),
            json.dumps(metrics),
        ],
    )
    con.close()
    return rid

def history(limit: int = 200) -> pd.DataFrame:
    init()
    con = _conn()
    df = con.execute(
        "SELECT id, ts, symbol, strategy, params, fees, metrics FROM runs ORDER BY ts DESC LIMIT ?",
        [limit],
    ).df()
    con.close()
    return df

