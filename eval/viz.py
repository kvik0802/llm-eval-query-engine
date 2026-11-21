"""Visualization helpers for eval reports."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from eval.schema import SuiteReport


def plot_case_scores(report: SuiteReport, out: str = "scores.png") -> str:
    cases = report.cases
    ids = [c.case_id for c in cases]
    scores = [c.final_score for c in cases]
    colors = ["#22c55e" if c.passed else "#ef4444" for c in cases]

    fig, ax = plt.subplots(figsize=(max(6, len(ids) * 0.9), 4))
    ax.bar(ids, scores, color=colors)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Final score")
    ax.set_title(f"Eval scores — {report.suite} (avg={report.avg_score})")
    ax.axhline(0.5, color="#9ca3af", linestyle="--", linewidth=1)
    for i, s in enumerate(scores):
        ax.text(i, s + 0.02, f"{s:.2f}", ha="center", fontsize=8)
    plt.xticks(rotation=30, ha="right", fontsize=8)
    plt.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def plot_judge_vs_human(report: SuiteReport, labels: dict, out: str = "judge_vs_human.png") -> str:
    xs, ys, labels_list = [], [], []
    for c in report.cases:
        if c.case_id in labels and c.judge is not None:
            xs.append(c.judge.score)
            ys.append(labels[c.case_id])
            labels_list.append(c.case_id)
    if not xs:
        return out
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(xs, ys, s=60, color="#3b82f6")
    for x, y, lab in zip(xs, ys, labels_list):
        ax.annotate(lab, (x, y), fontsize=7, xytext=(4, 4), textcoords="offset points")
    ax.plot([0, 1], [0, 1], "k--", alpha=0.4)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Judge score")
    ax.set_ylabel("Human score")
    ax.set_title("Judge vs Human")
    plt.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def write_html_dashboard(report: SuiteReport, charts: list[str], out: str = "dashboard.html") -> str:
    rows = "".join(
        f"<tr><td>{c.case_id}</td><td>{c.task}</td><td>{c.final_score}</td><td>{'pass' if c.passed else 'fail'}</td></tr>"
        for c in report.cases
    )
    imgs = "".join(f'<img src="{c}" style="max-width:100%;margin:10px 0"/>' for c in charts)
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Eval Dashboard</title>
<style>body{{font-family:sans-serif;margin:20px}} table{{border-collapse:collapse}} td,th{{border:1px solid #ccc;padding:6px}}</style>
</head><body>
<h1>Eval Dashboard — {report.suite}</h1>
<p>n={report.n} passed={report.passed} avg_score={report.avg_score}</p>
{imgs}
<table><tr><th>Case</th><th>Task</th><th>Score</th><th>Status</th></tr>{rows}</table>
</body></html>"""
    Path(out).write_text(html, encoding="utf-8")
    return out
