"""NL->SQL pipelines under test."""
from __future__ import annotations

import os
import re
import sqlite3
from eval.llm_client import call_llm


def _get_db_schema(db_path: str) -> str:
    """Introspect sqlite database schema to inject into prompt."""
    if not os.path.exists(db_path):
        return ""
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL;")
        tables = [row[0] for row in cur.fetchall()]
        conn.close()
        return "\n".join(tables)
    except Exception:
        return ""


def nl2sql(question: str, db_path: str) -> str:
    q = question.lower()
    variant = os.getenv("PIPELINE_VARIANT", "good")

    if variant == "poor":
        return "SELECT COUNT(*) FROM users"

    # If an actual LLM provider is configured and PIPELINE_MODE=llm, call LLM
    if os.getenv("PIPELINE_MODE", "rules").lower() == "llm":
        schema = _get_db_schema(db_path)
        system_prompt = (
            "You are a SQL expert. Generate a single valid SQLite query that answers the user question.\n"
            f"Database schema:\n{schema}\n"
            "Respond ONLY with the SQL query string, no Markdown code fences, no explanations."
        )
        response = call_llm(prompt=question, system_prompt=system_prompt, temperature=0.0)
        clean_sql = re.sub(r"^```sql\s*", "", response.strip(), flags=re.IGNORECASE)
        clean_sql = re.sub(r"^```\s*", "", clean_sql)
        clean_sql = re.sub(r"\s*```$", "", clean_sql).strip()
        if clean_sql:
            return clean_sql

    # Rule-based reference implementation (default or fallback)
    if "how many users" in q and "january" in q:
        return "SELECT COUNT(*) FROM users WHERE created_at LIKE '2024-01-%'"
    if "list all users" in q:
        return "SELECT id,name,created_at FROM users ORDER BY id"
    if "total order amount" in q and "alice" in q:
        return "SELECT SUM(amount) FROM orders WHERE user_id=1"
    if "how many orders" in q:
        return "SELECT COUNT(*) FROM orders"
    
    return "SELECT COUNT(*) FROM users"
