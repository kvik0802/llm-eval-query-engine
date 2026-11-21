# LLM Evaluation Framework for a Query Engine

Scores NL→SQL, metric, and document pipelines with **execution-based checks + an LLM judge**, validates the judge against human labels, persists evaluation run history, and runs in GitHub Actions as a quality gate.

## Features

- **Multi-task evaluation**: NL→SQL execution checks, metric numerical checks, and semantic document QA checks.
- **Hybrid evaluation**: Combines deterministic execution passes with automated multi-provider LLM judges (OpenAI, Anthropic, Gemini, Ollama, offline heuristic).
- **Concurrency & throughput**: Multi-threaded async evaluation runs with configurable workers.
- **Sandboxed execution**: Enforced read-only SQLite connections (`mode=ro`, `PRAGMA query_only = ON`) and interrupt query timeouts.
- **Persistent storage & trend tracking**: Historical runs tracked in SQLite (`eval_runs.db`) with trend charting in Streamlit.
- **Judge caching**: SHA-256 prompt hashing to cache verdicts and prevent duplicate API spend.

---

## Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# 2. Build sample SQLite database
python fixtures/make_db.py

# 3. Run evaluation across all suites
python -m eval.cli run --suite all --workers 4

# 4. View history of past evaluation runs
python -m eval.cli history

# 5. Launch the Streamlit interactive dashboard
streamlit run dashboard.py
```

---

## Configuration (`.env`)

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

| Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `GEMINI_API_KEY` | Google Gemini API key | - |
| `JUDGE_PROVIDER` | `auto`, `openai`, `anthropic`, `gemini`, `ollama`, or `heuristic` | `auto` |
| `PIPELINE_MODE` | `rules` (deterministic) or `llm` (real LLM generation) | `rules` |
| `PIPELINE_VARIANT` | `good` (normal) or `poor` (degraded quality for testing) | `good` |
| `EVAL_WORKERS` | Number of concurrent execution threads | `4` |

---

## CLI Commands

```bash
# Run eval and save report
leval run --suite all --out report.json --workers 4

# View recent runs
leval history --limit 10

# Generate Markdown report
leval markdown --suite all --out report.md

# Calibrate judge against human labels (Cohen's Kappa & Pearson r)
leval calibrate --labels eval/calibration/human_labels.jsonl

# Generate static charts and HTML dashboard
leval visualize --out-dir viz
```

---

## CI / Testing / Linting

```bash
# Run tests
pytest -v

# Run linter
ruff check .
```
