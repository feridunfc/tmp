import os
import tempfile
from datetime import datetime
from algo5.db import db_utils


def test_feature_upsert_unique():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        os.environ["ALGO5_DB_PATH"] = tmp.name
    db_utils.init_schema()
    r = ("AAPL", datetime(2024, 1, 1), "rsi", 1, 55.0)
    db_utils.upsert_feature([r, r])
    with db_utils.get_conn() as conn:
        c = conn.execute("SELECT COUNT(*) FROM features").fetchone()[0]
        assert c == 1
