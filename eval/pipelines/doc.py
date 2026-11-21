"""Document QA pipelines under test."""
from __future__ import annotations

import os
from eval.llm_client import call_llm


def answer_doc(question: str, context: str) -> str:
    variant = os.getenv("PIPELINE_VARIANT", "good")
    if variant == "poor":
        return "I don't know."

    # If an actual LLM provider is configured and PIPELINE_MODE=llm, call LLM
    if os.getenv("PIPELINE_MODE", "rules").lower() == "llm":
        system_prompt = (
            "You are a helpful assistant. Answer the user question accurately based ONLY on the provided context.\n"
            f"Context:\n{context}\n"
            "If the context does not contain the answer, say 'No answer.' Keep the answer concise."
        )
        response = call_llm(prompt=question, system_prompt=system_prompt, temperature=0.0)
        if response.strip():
            return response.strip()

    # Rule-based reference implementation (default or fallback)
    q = question.lower()
    if "refund" in q:
        return "Refunds are available within 30 days with a receipt; digital goods are non-refundable after download."
    if "password" in q:
        return "Click 'Forgot password' on the login page; a link is emailed and expires in 15 minutes."
    return "No answer."
