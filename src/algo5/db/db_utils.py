from __future__ import annotations
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Testlerde override edilebilsin:
DEFAULT_DB = Path(__file__).with_name("algo5.db")
DB_PATH = Path(os.environ.get("ALGO5_DB_PATH", str(DEFAULT_DB)))


def _enable_pragmas(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")


@contextmanager
def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES)
    try:
        _enable_pragmas(conn)
        yield conn
    finally:
        conn.close()


def init_schema() -> None:
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with get_conn() as conn:
        conn.executescript(schema)
        conn.commit()


# --- Convenience UPSERT helpers ---
def upsert_market_data(rows: list[tuple]) -> None:
    """
    rows: [(symbol, ts, open, high, low, close, volume), ...]
    """
    sql = """
    INSERT INTO market_data(symbol, ts, open, high, low, close, volume)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(symbol, ts) DO UPDATE SET
      open=excluded.open, high=excluded.high, low=excluded.low,
      close=excluded.close, volume=excluded.volume;
    """
    with get_conn() as conn:
        conn.executemany(sql, rows)
        conn.commit()


def upsert_feature(rows: list[tuple]) -> None:
    """
    rows: [(symbol, ts, name, version, value), ...]
    """
    sql = """
    INSERT INTO features(symbol, ts, name, version, value)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(symbol, ts, name, version) DO UPDATE SET
      value=excluded.value;
    """
    with get_conn() as conn:
        conn.executemany(sql, rows)
        conn.commit()
