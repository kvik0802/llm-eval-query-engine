"""Metric checks."""
from __future__ import annotations

from eval.schema import CheckResult


def check_metric(case, predicted: float) -> CheckResult:
    if case.gold_value is None:
        return CheckResult(name="metric_exact", passed=False, detail="missing gold")
    tol = 1e-6
    passed = abs(float(predicted) - float(case.gold_value)) <= tol
    return CheckResult(
        name="metric_exact",
        passed=passed,
        detail=f"got={predicted} expected={case.gold_value}",
        score=1.0 if passed else 0.0,
    )
