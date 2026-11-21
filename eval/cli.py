"""CLI entrypoint."""
from __future__ import annotations

import json
from pathlib import Path

import typer

from eval.calibration.agreement import compute_agreement, load_labels
from eval.runner import run_suite
from eval.storage import list_runs, record_run
from eval.viz import plot_case_scores, plot_judge_vs_human, write_html_dashboard

app = typer.Typer(help="LLM eval framework for a query engine")


@app.command()
def run(
    suite: str = "all",
    data_dir: str = "eval/datasets",
    out: str = "report.json",
    workers: int = typer.Option(4, help="Number of concurrent worker threads"),
    record: bool = typer.Option(True, help="Record run to persistent SQLite run storage"),
):
    dd = Path(data_dir)
    report = run_suite(suite, dd, max_workers=workers)
    Path(out).write_text(report.model_dump_json(indent=2))
    
    if record:
        run_id = record_run(report)
        print(f"Recorded run #{run_id} into eval_runs.db")

    print(f"suite={report.suite} n={report.n} passed={report.passed} avg_score={report.avg_score}")
    print(f"report written to {out}")


@app.command()
def history(limit: int = 10):
    """View historical evaluation runs."""
    runs = list_runs(limit=limit)
    if not runs:
        print("No evaluation runs found in history.")
        return
    print(f"{'ID':<6} {'Timestamp':<25} {'Suite':<10} {'Passed/Total':<15} {'Avg Score':<10}")
    print("-" * 70)
    for r in runs:
        pass_ratio = f"{r['passed_cases']}/{r['total_cases']}"
        print(f"{r['id']:<6} {r['timestamp'][:19]:<25} {r['suite']:<10} {pass_ratio:<15} {r['avg_score']:<10.4f}")


@app.command()
def markdown(suite: str = "all", data_dir: str = "eval/datasets", out: str = "report.md", workers: int = 4):
    dd = Path(data_dir)
    report = run_suite(suite, dd, max_workers=workers)
    lines = [f"# Eval Report — {report.suite}", "", f"- cases: {report.n}", f"- passed: {report.passed}", f"- avg score: {report.avg_score}", "", "## Cases", ""]
    for c in report.cases:
        lines.append(f"- **{c.case_id}** ({c.task}): score={c.final_score} passed={c.passed}")
        for ch in c.checks:
            lines.append(f"  - {ch.name}: {ch.passed} ({ch.detail})")
        if c.judge:
            lines.append(f"  - judge: {c.judge.score} — {c.judge.rationale}")
    Path(out).write_text("\n".join(lines))
    print(f"report written to {out}")


@app.command()
def calibrate(suite: str = "all", data_dir: str = "eval/datasets", labels: str = "eval/calibration/human_labels.jsonl", out: str = "calibration.json"):
    dd = Path(data_dir)
    report = run_suite(suite, dd)
    label_map = load_labels(Path(labels))
    js, hs = [], []
    for c in report.cases:
        if c.case_id in label_map:
            js.append(c.judge.score if c.judge else c.final_score)
            hs.append(label_map[c.case_id])
    res = compute_agreement(js, hs)
    Path(out).write_text(json.dumps(res, indent=2))
    print(res)


@app.command()
def visualize(suite: str = "all", data_dir: str = "eval/datasets", labels: str = "eval/calibration/human_labels.jsonl", out_dir: str = "viz"):
    import os

    from eval.calibration.agreement import load_labels
    dd = Path(data_dir)
    report = run_suite(suite, dd)
    os.makedirs(out_dir, exist_ok=True)
    scores_png = os.path.join(out_dir, "scores.png")
    jvh_png = os.path.join(out_dir, "judge_vs_human.png")
    plot_case_scores(report, scores_png)
    label_map = load_labels(Path(labels)) if Path(labels).exists() else {}
    plot_judge_vs_human(report, label_map, jvh_png)
    dash = os.path.join(out_dir, "dashboard.html")
    write_html_dashboard(report, [scores_png, jvh_png], dash)
    print(f"charts written to {out_dir}/ (scores.png, judge_vs_human.png, dashboard.html)")


if __name__ == "__main__":
    app()
