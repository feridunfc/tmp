# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd


def _to_iso(dt: Optional[Union[datetime, str]]) -> str:
    if dt is None:
        return datetime.utcnow().isoformat()
    if isinstance(dt, str):
        return dt
    return dt.isoformat()


def _jloads(s: Optional[str], default):
    try:
        return json.loads(s) if isinstance(s, str) and s else default
    except Exception:
        return default


@dataclass
class RunRecord:
    id: int
    experiment_id: int
    started_at: str
    finished_at: Optional[str]
    duration_sec: Optional[float]
    symbol: Optional[str]
    strategy: Optional[str]
    params_json: Optional[str]
    metrics_json: Optional[str]
    artifacts_json: Optional[str]
    status: Optional[str]
    notes: Optional[str]
    mode: Optional[str]


class ExperimentLogger:
    """
    SQLite tabanlı deney/koşu kayıtçısı (Arrow/Streamlit uyumlu).
    Şema:
      experiments(id, name UNIQUE, description, git_commit, tags_json, extra_json, created_at)
      runs(id, experiment_id FK, started_at, finished_at, duration_sec, symbol, strategy,
           params_json, metrics_json, artifacts_json, status, notes, mode)
    """

    def __init__(self, db_path: str = "results/experiments.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.artifacts_root = self.db_path.parent / "artifacts"
        self.artifacts_root.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.execute("PRAGMA journal_mode = WAL;")
        self._init_db()

    # ---------- DB init & migrate ----------
    def _init_db(self) -> None:
        cur = self.conn.cursor()
        # tablolar
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                description TEXT,
                git_commit TEXT,
                tags_json TEXT,
                extra_json TEXT,
                created_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY,
                experiment_id INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                duration_sec REAL,
                symbol TEXT,
                strategy TEXT,
                params_json TEXT,
                metrics_json TEXT,
                artifacts_json TEXT,
                status TEXT,
                notes TEXT,
                mode TEXT,
                FOREIGN KEY(experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
            )
            """
        )
        self.conn.commit()
        # migrate & index
        self._migrate_db()
        self._ensure_indexes()

    def _table_columns(self, table: str) -> List[str]:
        cur = self.conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        return [row[1] for row in cur.fetchall()]

    def _ensure_column(self, table: str, col: str, ddl: str) -> None:
        cols = self._table_columns(table)
        if col not in cols:
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
            self.conn.commit()

    def _migrate_db(self) -> None:
        # experiments
        self._ensure_column("experiments", "created_at", "TEXT")

        # runs
        for col, ddl in (
            ("finished_at", "TEXT"),
            ("duration_sec", "REAL"),
            ("symbol", "TEXT"),
            ("strategy", "TEXT"),
            ("params_json", "TEXT"),
            ("metrics_json", "TEXT"),
            ("artifacts_json", "TEXT"),
            ("status", "TEXT"),
            ("notes", "TEXT"),
            ("mode", "TEXT"),
        ):
            self._ensure_column("runs", col, ddl)
        try:
            self.conn.execute("UPDATE runs SET status = COALESCE(status, 'finished')")
            self.conn.commit()
        except Exception:
            pass

    def _ensure_indexes(self) -> None:
        cur = self.conn.cursor()
        for ddl in (
            "CREATE INDEX IF NOT EXISTS ix_runs_exp ON runs(experiment_id)",
            "CREATE INDEX IF NOT EXISTS ix_runs_time ON runs(started_at)",
            "CREATE INDEX IF NOT EXISTS ix_runs_sym ON runs(symbol)",
            "CREATE INDEX IF NOT EXISTS ix_runs_strategy ON runs(strategy)",
            "CREATE INDEX IF NOT EXISTS ix_runs_status ON runs(status)",
            "CREATE INDEX IF NOT EXISTS ix_runs_mode ON runs(mode)",
        ):
            try:
                cur.execute(ddl)
            except sqlite3.OperationalError:
                pass
        self.conn.commit()

    # ---------- Experiments ----------
    def create_experiment(
        self,
        name: str,
        description: Optional[str] = None,
        git_commit: Optional[str] = None,
        tags: Optional[List[str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO experiments(name, description, git_commit, tags_json, extra_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                description,
                git_commit,
                json.dumps(tags or []),
                json.dumps(extra or {}),
                _to_iso(None),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def ensure_experiment(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        git_commit: Optional[str] = None,
        tags: Optional[List[str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM experiments WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            return int(row["id"])
        return self.create_experiment(
            name=name,
            description=description,
            git_commit=git_commit,
            tags=tags,
            extra=extra,
        )

    def list_experiments(self, name_like: Optional[str] = None) -> pd.DataFrame:
        cur = self.conn.cursor()
        if name_like:
            cur.execute(
                """
                SELECT e.*,
                       (SELECT COUNT(1) FROM runs r WHERE r.experiment_id = e.id) AS run_count
                FROM experiments e
                WHERE e.name LIKE ?
                ORDER BY e.created_at DESC
                """,
                (f"%{name_like}%",),
            )
        else:
            cur.execute(
                """
                SELECT e.*,
                       (SELECT COUNT(1) FROM runs r WHERE r.experiment_id = e.id) AS run_count
                FROM experiments e
                ORDER BY e.created_at DESC
                """
            )
        rows = cur.fetchall()
        df = pd.DataFrame([dict(r) for r in rows])
        for col in ("tags_json", "extra_json"):
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: json.loads(x) if isinstance(x, str) and x else ([] if col == "tags_json" else {})
                )
        return df

    # ---------- Runs ----------
    def start_run(
        self,
        experiment_id: int,
        *,
        symbol: Optional[str] = None,
        strategy: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        status: str = "running",
        notes: Optional[str] = None,
        mode: Optional[str] = None,
        started_at: Optional[Union[str, datetime]] = None,
        **kwargs,
    ) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO runs(experiment_id, started_at, finished_at, duration_sec,
                             symbol, strategy, params_json, metrics_json, artifacts_json, status, notes, mode)
            VALUES (?, ?, NULL, NULL, ?, ?, ?, NULL, NULL, ?, ?, ?)
            """,
            (
                experiment_id,
                _to_iso(started_at),
                symbol,
                strategy,
                json.dumps(params or {}),
                status,
                notes,
                mode,
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def _normalize_artifacts(self, artifacts: Optional[Union[Dict[str, Any], List[str]]]) -> Dict[str, Any]:
        if artifacts is None:
            return {}
        if isinstance(artifacts, dict):
            return artifacts
        # list -> dict'e çevir (dosya adlarından anahtar üret)
        out: Dict[str, Any] = {}
        for p in artifacts:
            self._art_key_add(out, str(p))
        return out

    def finish_run(
        self,
        run_id: int,
        *,
        metrics: Optional[Dict[str, Any]] = None,
        artifacts: Optional[Union[Dict[str, Any], List[str]]] = None,
        status: str = "finished",
        notes: Optional[str] = None,
        finished_at: Optional[Union[str, datetime]] = None,
    ) -> None:
        cur = self.conn.cursor()
        cur.execute("SELECT started_at FROM runs WHERE id = ?", (run_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"finish_run: run_id {run_id} bulunamadı")

        started_dt = datetime.fromisoformat(str(row["started_at"]))
        finished_iso = _to_iso(finished_at)
        finished_dt = datetime.fromisoformat(finished_iso)
        duration = (finished_dt - started_dt).total_seconds()

        cur.execute(
            """
            UPDATE runs
               SET finished_at = ?, duration_sec = ?,
                   metrics_json = ?, artifacts_json = ?,
                   status = ?, notes = COALESCE(?, notes)
             WHERE id = ?
            """,
            (
                finished_iso,
                float(duration),
                json.dumps(metrics or {}),
                json.dumps(self._normalize_artifacts(artifacts)),
                status,
                notes,
                run_id,
            ),
        )
        self.conn.commit()

    def log_run(
        self,
        experiment_name: str,
        *,
        symbol: Optional[str],
        strategy: Optional[str],
        params: Optional[Dict[str, Any]],
        metrics: Optional[Dict[str, Any]],
        artifacts: Optional[Dict[str, Any]] = None,
        git_commit: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: str = "finished",
        notes: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> int:
        exp_id = self.ensure_experiment(
            experiment_name, git_commit=git_commit, tags=tags
        )
        run_id = self.start_run(
            exp_id,
            symbol=symbol,
            strategy=strategy,
            params=params,
            status="running",
            notes=notes,
            mode=mode,
        )
        self.finish_run(
            run_id, metrics=metrics, artifacts=artifacts, status=status, notes=notes
        )
        return run_id

    def get_run(self, run_id: int) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"run {run_id} bulunamadı")
        rec = dict(row)
        # JSON'ları string olarak bırak; istenirse ayrı çek
        return rec

    def list_runs(
        self,
        *,
        experiment_id=None, symbol=None, strategy=None,
        status=None, mode=None, since=None, until=None,
        limit: int = 200, order: str = "desc"
    ) -> pd.DataFrame:
        where, params = [], []
        if experiment_id is not None: where.append("experiment_id=?"); params.append(experiment_id)
        if symbol: where.append("symbol=?"); params.append(symbol)
        if strategy: where.append("strategy=?"); params.append(strategy)
        if status: where.append("status=?"); params.append(status)
        if mode: where.append("mode=?"); params.append(mode)
        if since: where.append("started_at>=?"); params.append(_to_iso(since))
        if until: where.append("started_at<=?"); params.append(_to_iso(until))
        where_sql = ("WHERE " + " AND ".join(where)) if where else ""
        order_sql = "DESC" if str(order).lower().startswith("d") else "ASC"
        limit_sql = f"LIMIT {int(limit)}" if limit and limit > 0 else ""
        sql = f"""
            SELECT id, experiment_id, started_at, finished_at, duration_sec,
                   symbol, strategy, params_json, metrics_json, artifacts_json,
                   status, notes, mode
              FROM runs {where_sql}
          ORDER BY started_at {order_sql} {limit_sql}
        """
        cur = self.conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        df = pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame(
            columns=["id","experiment_id","started_at","finished_at","duration_sec",
                     "symbol","strategy","params_json","metrics_json","artifacts_json",
                     "status","notes","mode"]
        )
        # Arrow uyumu: tarihleri stringle
        for c in ("started_at", "finished_at"):
            if c in df.columns:
                df[c] = df[c].astype(str)
        return df

    def get_artifacts(self, run_id: int) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute("SELECT artifacts_json FROM runs WHERE id = ?", (run_id,))
        row = cur.fetchone()
        if not row:
            return {}
        val = row["artifacts_json"]
        if not val:
            return {}
        obj = val
        if isinstance(val, str):
            try:
                obj = json.loads(val)
            except Exception:
                obj = {}
        if isinstance(obj, list):
            result: Dict[str, str] = {}
            for p in obj:
                self._art_key_add(result, str(p))
            return result
        if isinstance(obj, dict):
            return obj
        return {}

    @staticmethod
    def _art_key_add(result: Dict[str, str], path: str) -> None:
        try:
            name = os.path.basename(path)
            stem, ext = os.path.splitext(name)
            extc = ext.lstrip(".").lower()
            for k in {stem, name, (f"{stem}_{extc}" if extc else stem)}:
                if k not in result:
                    result[k] = path
        except Exception:
            pass
