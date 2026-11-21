"""Document QA checks (token overlap + semantic similarity)."""
from __future__ import annotations

import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from eval.schema import CheckResult


def _tokens(s: str):
    return set(re.findall(r"\w+", s.lower()))


def check_doc(case, predicted: str) -> CheckResult:
    if not case.gold_answer:
        return CheckResult(name="doc_overlap", passed=False, detail="missing gold")
    gold_t = _tokens(case.gold_answer)
    pred_t = _tokens(predicted)
    if not gold_t:
        overlap = 1.0
    else:
        overlap = len(gold_t & pred_t) / len(gold_t)
    passed = overlap >= 0.5
    return CheckResult(
        name="doc_overlap",
        passed=passed,
        detail=f"overlap={overlap:.2f}",
        score=overlap,
    )


def check_doc_semantic(case, predicted: str) -> CheckResult:
    if not case.gold_answer:
        return CheckResult(name="doc_semantic", passed=False, detail="missing gold")
    try:
        vec = TfidfVectorizer().fit_transform([case.gold_answer, predicted])
        sim = float(cosine_similarity(vec[0:1], vec[1:2])[0][0])
    except Exception as e:
        return CheckResult(name="doc_semantic", passed=False, detail=f"error: {e}", score=0.0)
    passed = sim >= 0.5
    return CheckResult(
        name="doc_semantic",
        passed=passed,
        detail=f"cosine={sim:.2f}",
        score=sim,
    )
