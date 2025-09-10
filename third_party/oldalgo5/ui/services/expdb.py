import sqlite3, json, time
from ui.services.paths import db_path, equities_dir
def _ensure(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS runs(
        id TEXT PRIMARY KEY, ts REAL, strategy TEXT, params TEXT, metrics TEXT, symbols TEXT, equity_csv TEXT
    )""")
def write_run(*, run_id, strategy, params, metrics, symbols, equity_series):
    conn = sqlite3.connect(db_path())
    try:
        _ensure(conn); csv_file = equities_dir()/f"{run_id}.csv"
        equity_series.to_frame("equity").to_csv(csv_file, index=True)
        conn.execute("INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?,?,?)",
                     (run_id, time.time(), strategy, json.dumps(params), json.dumps(metrics), json.dumps(symbols), str(csv_file)))
        conn.commit(); return run_id
    finally: conn.close()
def list_runs(limit=100):
    conn = sqlite3.connect(db_path())
    try:
        _ensure(conn)
        rows = conn.execute("SELECT id, ts, strategy, params, metrics, symbols, equity_csv FROM runs ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
        import json
        return [{"id":r[0],"ts":r[1],"strategy":r[2],"params":json.loads(r[3]),"metrics":json.loads(r[4]),"symbols":json.loads(r[5]),"equity_csv":r[6]} for r in rows]
    finally: conn.close()
