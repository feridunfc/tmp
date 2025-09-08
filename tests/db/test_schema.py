import os
import tempfile
from datetime import datetime
from algo5.db import db_utils


def _tmpdb():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        os.environ["ALGO5_DB_PATH"] = tmp.name
        return tmp.name


def test_tables_exist_and_fk():
    _tmpdb()
    db_utils.init_schema()
    with db_utils.get_conn() as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"market_data", "features", "runs", "watchlist", "orders", "fills"}.issubset(tables)
        try:
            conn.execute(
                "INSERT INTO fills(fill_id,order_id,ts,qty,price) VALUES (?,?,?,?,?)",
                ("f1", "missing", datetime.utcnow(), 1, 100.0),
            )
            conn.commit()
            raise AssertionError("FK should fail")
        except Exception:
            conn.rollback()
