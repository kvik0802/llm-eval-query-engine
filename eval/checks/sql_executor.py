"""Secure execution-based SQL checks with timeouts and read-only enforcement."""
from __future__ import annotations

import sqlite3
import threading
from typing import Any

from eval.schema import CheckResult


def run_sql(db_path: str, sql: str, timeout_seconds: float = 3.0) -> list[list[Any]]:
    """Execute SQL query safely with read-only constraint and query timeout."""
    clean_path = db_path.replace("\\", "/")
    uri = f"file:{clean_path}?mode=ro"
    
    conn = sqlite3.connect(uri, uri=True, timeout=timeout_seconds)
    try:
        try:
            conn.execute("PRAGMA query_only = ON;")
        except Exception:
            pass

        timed_out = [False]
        def interrupt_handler():
            timed_out[0] = True
            conn.interrupt()

        timer = threading.Timer(timeout_seconds, interrupt_handler)
        timer.start()
        try:
            cur = conn.execute(sql)
            rows = [list(r) for r in cur.fetchall()]
            return rows
        except sqlite3.OperationalError as e:
            if timed_out[0] or "interrupted" in str(e).lower():
                raise TimeoutError(f"Query timed out after {timeout_seconds}s") from e
            raise
        finally:
            timer.cancel()
    finally:
        conn.close()


def check_sql(case, predicted_sql: str) -> CheckResult:
    if case.expected_rows is None or case.db is None:
        return CheckResult(name="sql_execution", passed=False, detail="missing gold")
    try:
        got = run_sql(case.db, predicted_sql)
    except Exception as e:
        return CheckResult(name="sql_execution", passed=False, detail=f"error: {e}")

    def norm(v):
        if isinstance(v, float):
            return round(v, 6)
        return v

    got_n = [[norm(x) for x in r] for r in got]
    exp_n = [[norm(x) for x in r] for r in case.expected_rows]
    passed = got_n == exp_n
    return CheckResult(
        name="sql_execution",
        passed=passed,
        detail=f"got={got_n} expected={exp_n}",
        score=1.0 if passed else 0.0,
    )
