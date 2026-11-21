"""Evaluation runner supporting concurrent execution and batch processing."""
from __future__ import annotations

import concurrent.futures
import os
from pathlib import Path

from eval.checks.doc_checker import check_doc, check_doc_semantic
from eval.checks.metric_checker import check_metric
from eval.checks.sql_executor import check_sql
from eval.judge.llm_judge import judge
from eval.pipelines import doc as doc_pipe
from eval.pipelines import metric as metric_pipe
from eval.pipelines import nl2sql as nl2sql_pipe
from eval.schema import CaseResult, EvalCase, SuiteReport


def load_cases(path: Path) -> list[EvalCase]:
    cases = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(EvalCase.model_validate_json(line))
    return cases


def run_case(case: EvalCase) -> CaseResult:
    if case.task == "nl2sql":
        sql = nl2sql_pipe.nl2sql(case.input, case.db or "")
        checks = [check_sql(case, sql)]
        output = sql
    elif case.task == "metric":
        val = metric_pipe.compute_metric(case.metric_name or "", case.context or "")
        checks = [check_metric(case, val)]
        output = val
    elif case.task == "doc":
        ans = doc_pipe.answer_doc(case.input, case.context or "")
        checks = [check_doc(case, ans), check_doc_semantic(case, ans)]
        output = ans
    else:
        checks = []
        output = None

    v = judge(case, output, checks)
    exec_pass = all(c.passed for c in checks) if checks else True
    final = v.score if checks else (1.0 if exec_pass else 0.0)
    
    # Hybrid evaluation: require execution pass for full credit
    if checks and not exec_pass:
        final = min(final, 0.5)
    passed = (final >= 0.5) and (exec_pass if checks else True)

    return CaseResult(
        case_id=case.id,
        task=case.task,
        pipeline_output=output,
        checks=checks,
        judge=v,
        final_score=round(final, 4),
        passed=passed,
    )


def run_suite(suite: str, data_dir: Path, max_workers: int | None = None) -> SuiteReport:
    file_map = {
        "nl2sql": data_dir / "nl2sql.jsonl",
        "metric": data_dir / "metric.jsonl",
        "doc": data_dir / "docs.jsonl",
    }
    if suite == "all":
        cases: list[EvalCase] = []
        for p in file_map.values():
            cases.extend(load_cases(p))
    else:
        cases = load_cases(file_map[suite])

    workers = max_workers or int(os.getenv("EVAL_WORKERS", "4"))
    
    if workers > 1 and len(cases) > 1:
        # Concurrent execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(run_case, cases))
    else:
        results = [run_case(c) for c in cases]

    passed = sum(1 for r in results if r.passed)
    avg = sum(r.final_score for r in results) / len(results) if results else 0.0
    return SuiteReport(suite=suite, n=len(results), passed=passed, avg_score=round(avg, 4), cases=results)
