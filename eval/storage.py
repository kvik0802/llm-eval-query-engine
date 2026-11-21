"""Persistent storage and tracking for evaluation runs."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from eval.schema import SuiteReport

DEFAULT_DB_PATH = "eval_runs.db"


def init_storage(db_path: str = DEFAULT_DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        suite TEXT NOT NULL,
        total_cases INTEGER NOT NULL,
        passed_cases INTEGER NOT NULL,
        avg_score REAL NOT NULL,
        report_json TEXT NOT NULL
    );
    """)
    conn.commit()
    conn.close()


def record_run(report: SuiteReport, db_path: str = DEFAULT_DB_PATH) -> int:
    init_storage(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    ts = datetime.now(timezone.utc).isoformat()
    cur.execute(
        "INSERT INTO runs (timestamp, suite, total_cases, passed_cases, avg_score, report_json) VALUES (?, ?, ?, ?, ?, ?)",
        (ts, report.suite, report.n, report.passed, report.avg_score, report.model_dump_json()),
    )
    run_id = cur.lastrowid or 0
    conn.commit()
    conn.close()
    return run_id


def list_runs(limit: int = 10, db_path: str = DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    if not Path(db_path).exists():
        return []
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, timestamp, suite, total_cases, passed_cases, avg_score FROM runs ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "timestamp": r[1],
            "suite": r[2],
            "total_cases": r[3],
            "passed_cases": r[4],
            "avg_score": r[5],
        }
        for r in rows
    ]
