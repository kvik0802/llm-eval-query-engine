from pathlib import Path

from eval.runner import run_suite


def test_good_pipeline_passes():
    r = run_suite("all", Path("eval/datasets"))
    assert r.n == 9
    assert r.passed >= 8
    assert r.avg_score > 0.9
