"""LLM judge with multi-provider support, caching, and offline fallback."""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from eval.llm_client import call_llm
from eval.schema import JudgeVerdict

_JUDGE_CACHE: dict[str, JudgeVerdict] = {}


def _heuristic_judge(case: Any, output: Any, checks: list[Any]) -> JudgeVerdict:
    if checks:
        exec_score = sum(c.score for c in checks) / len(checks)
    else:
        exec_score = 1.0
    score = min(1.0, max(0.0, exec_score))
    return JudgeVerdict(score=score, rationale="offline heuristic judge", dimensions={"correctness": score})


def _prompt(case: Any, output: Any, checks: list[Any]) -> str:
    gold = getattr(case, "gold_sql", None) or getattr(case, "gold_value", None) or getattr(case, "gold_answer", None)
    return f"""You are an evaluation judge. Score the pipeline output for task '{case.task}'.

Input: {case.input}
Output: {json.dumps(output, default=str)}
Checks: {[c.model_dump() for c in checks]}
Gold (if any): {gold}

Return JSON only: {{"score": 0.0-1.0, "rationale": "...", "dimensions": {{"correctness": 0.0-1.0, "completeness": 0.0-1.0}}}}"""


def _parse(text: str) -> JudgeVerdict:
    try:
        data = json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        data = json.loads(text[start:end+1]) if start >= 0 and end > start else {}
    return JudgeVerdict(
        score=float(data.get("score", 0.0)),
        rationale=data.get("rationale", ""),
        dimensions=data.get("dimensions", {}),
    )


def judge(case: Any, output: Any, checks: list[Any], use_cache: bool = True) -> JudgeVerdict:
    prompt = _prompt(case, output, checks)
    cache_key = hashlib.sha256(f"{prompt}_{os.getenv('JUDGE_PROVIDER', '')}_{os.getenv('JUDGE_MODEL', '')}".encode()).hexdigest()

    if use_cache and cache_key in _JUDGE_CACHE:
        return _JUDGE_CACHE[cache_key]

    provider = os.getenv("JUDGE_PROVIDER", "").lower()
    if provider in ("", "auto"):
        if os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        elif os.getenv("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        elif os.getenv("GEMINI_API_KEY"):
            provider = "gemini"
        elif os.getenv("OLLAMA_URL"):
            provider = "ollama"
        else:
            verdict = _heuristic_judge(case, output, checks)
            if use_cache:
                _JUDGE_CACHE[cache_key] = verdict
            return verdict

    if provider == "heuristic":
        return _heuristic_judge(case, output, checks)

    model = os.getenv("JUDGE_MODEL")
    try:
        text = call_llm(
            prompt=prompt,
            system_prompt="You are an unbiased automated LLM judge scoring model evaluation benchmarks.",
            provider=provider,
            model=model,
            temperature=0.0,
            json_mode=True,
        )
        if not text:
            verdict = _heuristic_judge(case, output, checks)
        else:
            verdict = _parse(text)
    except Exception as e:
        verdict = _heuristic_judge(case, output, checks)
        verdict.rationale = f"judge error ({e}); fallback heuristic"

    if use_cache:
        _JUDGE_CACHE[cache_key] = verdict
    return verdict
