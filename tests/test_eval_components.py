"""Comprehensive test suite for evaluation framework components."""
from pathlib import Path
from eval.checks.sql_executor import check_sql
from eval.checks.doc_checker import check_doc
from eval.checks.metric_checker import check_metric
from eval.judge.llm_judge import judge
from eval.schema import EvalCase
from eval.storage import record_run, list_runs
from eval.runner import run_suite


def test_sql_executor_timeout_and_readonly(tmp_path):
    db_file = str(tmp_path / "test.db")
    import sqlite3
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE t (id INT);")
    conn.commit()
    conn.close()

    # Mutation should fail under read-only mode
    case_mutation = EvalCase(
        id="test_mut",
        task="nl2sql",
        input="insert",
        db=db_file,
        expected_rows=[],
    )
    res = check_sql(case_mutation, "INSERT INTO t VALUES (1);")
    assert not res.passed
    assert "error" in res.detail.lower()

    # Read queries succeed
    case_read = EvalCase(
        id="test_read",
        task="nl2sql",
        input="select",
        db=db_file,
        expected_rows=[],
    )
    res_read = check_sql(case_read, "SELECT * FROM t;")
    assert res_read.passed


def test_doc_checks():
    case = EvalCase(
        id="c1",
        task="doc",
        input="refund policy",
        gold_answer="Refunds within 30 days with receipt.",
    )
    # Good answer
    res_overlap = check_doc(case, "You can get refunds within 30 days with receipt.")
    assert res_overlap.passed
    assert res_overlap.score > 0.5

    # Completely wrong answer
    res_wrong = check_doc(case, "Never available.")
    assert not res_wrong.passed


def test_metric_checks():
    case = EvalCase(
        id="m1",
        task="metric",
        input="revenue",
        gold_value=100.0,
    )
    assert check_metric(case, 100.0).passed
    assert not check_metric(case, 95.0).passed


def test_heuristic_judge_and_caching():
    case = EvalCase(
        id="c1",
        task="metric",
        input="rev",
        gold_value=10.0,
    )
    v1 = judge(case, 10.0, [], use_cache=True)
    assert v1.score == 1.0
    v2 = judge(case, 10.0, [], use_cache=True)
    assert v1 == v2


def test_storage(tmp_path):
    db_file = str(tmp_path / "runs.db")
    suite_res = run_suite("nl2sql", Path("eval/datasets"), max_workers=2)
    run_id = record_run(suite_res, db_path=db_file)
    assert run_id > 0
    runs = list_runs(limit=5, db_path=db_file)
    assert len(runs) == 1
    assert runs[0]["suite"] == "nl2sql"
