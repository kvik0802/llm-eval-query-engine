"""Pydantic schemas for eval cases and results."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EvalCase(BaseModel):
    id: str
    task: str  # nl2sql | metric | doc
    input: str
    # NL->SQL
    gold_sql: str | None = None
    db: str | None = None
    expected_rows: list[list[Any]] | None = None
    # metric
    gold_value: Any | None = None
    metric_name: str | None = None
    # doc
    gold_answer: str | None = None
    context: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CheckResult(BaseModel):
    name: str
    passed: bool
    detail: str = ""
    score: float = 0.0


class JudgeVerdict(BaseModel):
    score: float  # 0..1
    rationale: str
    dimensions: dict[str, float] = Field(default_factory=dict)


class CaseResult(BaseModel):
    case_id: str
    task: str
    pipeline_output: Any
    checks: list[CheckResult] = Field(default_factory=list)
    judge: JudgeVerdict | None = None
    final_score: float = 0.0
    passed: bool = False


class SuiteReport(BaseModel):
    suite: str
    n: int
    passed: int
    avg_score: float
    cases: list[CaseResult] = Field(default_factory=list)
    baseline_delta: float | None = None
