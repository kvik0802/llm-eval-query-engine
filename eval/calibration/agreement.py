"""Judge-vs-human agreement."""
from __future__ import annotations

import json
from pathlib import Path

from sklearn.metrics import accuracy_score, cohen_kappa_score


def load_labels(path: Path) -> dict[str, float]:
    out = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                d = json.loads(line)
                out[d["case_id"]] = float(d["human_score"])
    return out


def compute_agreement(judge_scores: list[float], human_scores: list[float]) -> dict:
    # binarize at 0.5
    j = [1 if s >= 0.5 else 0 for s in judge_scores]
    h = [1 if s >= 0.5 else 0 for s in human_scores]
    acc = accuracy_score(h, j) if h else 0.0
    try:
        kappa = cohen_kappa_score(h, j)
    except Exception:
        kappa = 0.0
    mae = sum(abs(a - b) for a, b in zip(judge_scores, human_scores)) / len(judge_scores) if judge_scores else 0.0
    return {"accuracy": round(acc, 4), "cohen_kappa": round(kappa, 4), "mae": round(mae, 4), "n": len(judge_scores)}
