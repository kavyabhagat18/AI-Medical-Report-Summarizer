"""
llm_orchestrator.py
--------------------
Owner: Member 2 (LLM Integration)

This is the SINGLE function the backend team should call. It hides the
Gemini/OpenAI split entirely -- tries Gemini first, falls back to OpenAI
if Gemini fails (rate limit, timeout, or any LLMError), and raises only
if both fail.

Backend usage (in backend/services/ai_service.py):

    from ai_summary.llm_orchestrator import get_llm_summary
    from ai_summary.prompt import build_prompt

    prompt = build_prompt(medical_data)
    result = get_llm_summary(prompt, medical_data)
    # result.text -> pass to summarizer.create_summary()
"""

import logging

from base_llm import LLMResult, LLMError
import gemini_api
import openai_api

logger = logging.getLogger(__name__)


def get_llm_summary(prompt: str, medical_data: dict, prefer: str = "gemini") -> LLMResult:
    """
    Calls the preferred LLM provider first, falls back to the other one
    if the first fails for any reason.

    Args:
        prompt: output of prompt.build_prompt(medical_data)
        medical_data: the structured JSON from Medical Information Extraction
        prefer: "gemini" (default) or "openai" -- which provider to try first

    Returns:
        LLMResult from whichever provider succeeded.

    Raises:
        LLMError if BOTH providers fail.
    """
    providers = {
        "gemini": gemini_api.generate_summary,
        "openai": openai_api.generate_summary,
    }

    order = ["gemini", "openai"] if prefer == "gemini" else ["openai", "gemini"]

    last_error = None
    for name in order:
        try:
            return providers[name](prompt, medical_data)
        except LLMError as e:
            logger.warning("%s failed, trying next provider if available: %s", name, e)
            last_error = e

    raise last_error or LLMError("Both Gemini and OpenAI failed to generate a summary.")
