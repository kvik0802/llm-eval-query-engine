"""Streamlit interactive dashboard for the eval framework."""
from __future__ import annotations

import json
import os
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from eval.calibration.agreement import compute_agreement, load_labels
from eval.runner import run_suite
from eval.storage import list_runs

st.set_page_config(page_title="LLM Eval Dashboard", layout="wide")
st.title("LLM Evaluation Dashboard")

with st.sidebar:
    st.header("Controls")
    suite = st.selectbox("Suite", ["all", "nl2sql", "metric", "doc"])
    pipeline_mode = st.selectbox("Pipeline mode", ["rules", "llm"], index=0)
    os.environ["PIPELINE_MODE"] = pipeline_mode
    variant = st.selectbox("Pipeline variant", ["good", "poor"])
    os.environ["PIPELINE_VARIANT"] = variant

    workers = st.slider("Workers (concurrency)", min_value=1, max_value=8, value=4)
    os.environ["EVAL_WORKERS"] = str(workers)

    st.subheader("LLM Provider & API Keys")
    provider = st.selectbox("Judge / LLM provider", ["auto", "openai", "anthropic", "gemini", "ollama", "heuristic"])
    openai_key = st.text_input("OpenAI API key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    anthropic_key = st.text_input("Anthropic API key", type="password", value=os.getenv("ANTHROPIC_API_KEY", ""))
    gemini_key = st.text_input("Gemini API key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
    ollama_url = st.text_input("Ollama URL", value=os.getenv("OLLAMA_URL", "http://localhost:11434"))
    judge_model = st.text_input("Model (optional)", value=os.getenv("JUDGE_MODEL", ""))

    if openai_key.strip():
        os.environ["OPENAI_API_KEY"] = openai_key.strip()
    if anthropic_key.strip():
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key.strip()
    if gemini_key.strip():
        os.environ["GEMINI_API_KEY"] = gemini_key.strip()
    if ollama_url.strip():
        os.environ["OLLAMA_URL"] = ollama_url.strip()
    if judge_model.strip():
        os.environ["JUDGE_MODEL"] = judge_model.strip()
    else:
        os.environ.pop("JUDGE_MODEL", None)

    if provider != "auto":
        os.environ["JUDGE_PROVIDER"] = provider
    else:
        os.environ.pop("JUDGE_PROVIDER", None)

    labels_path = st.text_input("Human labels", "eval/calibration/human_labels.jsonl")
    run_btn = st.button("Run evaluation")

if "report" not in st.session_state:
    st.session_state.report = None

if run_btn:
    with st.spinner("Running evaluation..."):
        report = run_suite(suite, Path("eval/datasets"), max_workers=workers)
        st.session_state.report = report

# Historical Runs Tab / Section
history_tab, current_tab = st.tabs(["Current Evaluation Run", "Historical Runs"])

with history_tab:
    report = st.session_state.report
    if report is None:
        st.info("Click 'Run evaluation' to start.")
    else:
        # Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Cases", report.n)
        c2.metric("Passed", report.passed)
        c3.metric("Avg score", f"{report.avg_score:.3f}")

        # Bar chart
        df = [{"case": c.case_id, "score": c.final_score, "status": "pass" if c.passed else "fail", "task": c.task} for c in report.cases]
        fig = px.bar(df, x="case", y="score", color="status", hover_data=["task"],
                     color_discrete_map={"pass": "#22c55e", "fail": "#ef4444"},
                     title="Per-case scores")
        fig.add_hline(y=0.5, line_dash="dash", line_color="gray")
        st.plotly_chart(fig, use_container_width=True)

        # Judge vs human
        if Path(labels_path).exists():
            label_map = load_labels(Path(labels_path))
            xs, ys, names = [], [], []
            for c in report.cases:
                if c.case_id in label_map and c.judge is not None:
                    xs.append(c.judge.score)
                    ys.append(label_map[c.case_id])
                    names.append(c.case_id)
            if xs:
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text", text=names, textposition="top center"))
                fig2.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line={"dash": "dash", "color": "gray"}, name="perfect"))
                fig2.update_layout(title="Judge vs Human", xaxis_title="Judge score", yaxis_title="Human score",
                                   xaxis={"range": [0, 1.05]}, yaxis={"range": [0, 1.05]})
                st.plotly_chart(fig2, use_container_width=True)
                js = [c.judge.score if c.judge else c.final_score for c in report.cases if c.case_id in label_map]
                hs = [label_map[c.case_id] for c in report.cases if c.case_id in label_map]
                st.json(compute_agreement(js, hs))

        # Case table
        st.subheader("Cases")
        st.dataframe([
            {"case": c.case_id, "task": c.task, "score": c.final_score, "passed": c.passed,
             "judge": (c.judge.score if c.judge else None), "checks": ", ".join(f"{ch.name}:{ch.passed}" for ch in c.checks)}
            for c in report.cases
        ], use_container_width=True)

        # Baseline comparison
        if Path("baseline.json").exists():
            base = json.loads(Path("baseline.json").read_text())
            delta = report.avg_score - base["avg_score"]
            st.metric("Delta vs baseline", f"{delta:+.3f}", delta_color="normal" if delta >= -0.02 else "inverse")

with current_tab:
    st.subheader("Historical Run Log")
    runs = list_runs(limit=25)
    if not runs:
        st.info("No recorded runs in eval_runs.db yet.")
    else:
        st.dataframe(runs, use_container_width=True)
        if len(runs) > 1:
            chronological = list(reversed(runs))
            hist_fig = px.line(
                chronological,
                x="timestamp",
                y="avg_score",
                markers=True,
                title="Average Score Trend Across Evaluation Runs",
            )
            hist_fig.update_layout(yaxis={"range": [0, 1.05]})
            st.plotly_chart(hist_fig, use_container_width=True)
