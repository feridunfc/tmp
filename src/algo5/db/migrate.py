from __future__ import annotations
from pathlib import Path
from .db_utils import get_conn

MIGRATIONS_DIR = Path(__file__).with_name("migrations")


def ensure_table(conn):
    conn.execute(
        """
    CREATE TABLE IF NOT EXISTS schema_migrations (
      version TEXT PRIMARY KEY,
      applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )


def applied_versions(conn) -> set[str]:
    cur = conn.execute("SELECT version FROM schema_migrations")
    return {r[0] for r in cur.fetchall()}


def run():
    MIGRATIONS_DIR.mkdir(exist_ok=True)
    with get_conn() as conn:
        ensure_table(conn)
        done = applied_versions(conn)
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            v = path.stem
            if v in done:
                continue
            conn.executescript(path.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migrations(version) VALUES (?)", (v,))
        conn.commit()


if __name__ == "__main__":
    run()
