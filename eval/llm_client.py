"""Client factory and unified LLM caller supporting OpenAI, Anthropic, Gemini, and Ollama."""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any


def call_llm(
    prompt: str,
    system_prompt: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.0,
    json_mode: bool = False,
) -> str:
    """Unified LLM call function with provider auto-detection and fallback."""
    provider = (provider or os.getenv("LLM_PROVIDER") or os.getenv("JUDGE_PROVIDER") or "").lower()

    if not provider:
        if os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        elif os.getenv("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        elif os.getenv("GEMINI_API_KEY"):
            provider = "gemini"
        elif os.getenv("OLLAMA_URL"):
            provider = "ollama"
        else:
            provider = "mock"

    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        m = model or "gpt-4o-mini"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        kwargs: dict[str, Any] = {"model": m, "messages": messages, "temperature": temperature}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

    elif provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        m = model or "claude-3-5-haiku-latest"
        kwargs = {
            "model": m,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        resp = client.messages.create(**kwargs)
        return resp.content[0].text

    elif provider == "gemini":
        from google import genai
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        m = model or "gemini-2.0-flash"
        contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        resp = client.models.generate_content(model=m, contents=contents)
        return resp.text or ""

    elif provider == "ollama":
        url = os.getenv("OLLAMA_URL", "http://localhost:11434") + "/api/generate"
        m = model or "llama3.2"
        payload = {"model": m, "prompt": prompt, "stream": False}
        if system_prompt:
            payload["system"] = system_prompt
        if json_mode:
            payload["format"] = "json"
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        return data.get("response", "")

    else:
        # Mock / fallback offline mode
        return ""
