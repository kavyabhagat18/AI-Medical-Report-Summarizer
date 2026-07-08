"""
base_llm.py
-----------
Owner: Member 2 (LLM Integration) - shared by gemini_api.py and openai_api.py

Why this file exists:
Both gemini_api.py and openai_api.py implement the SAME function signature
and raise the SAME exception types. This means the backend team (or
Member 3) can call whichever provider is configured -- or fall back from
one to the other -- without changing any other code.

CONTRACT (agreed with Member 1 and Member 3):
    Input  -> prompt: str (from prompt.build_prompt), medical_data: dict
    Output -> LLMResult (see below). LLMResult.text is the raw string
              the LLM returned (expected to be JSON, per prompt.py's
              instructions -- but summarizer.py must handle it not being
              perfectly valid JSON, since LLMs occasionally misbehave).
"""

from dataclasses import dataclass


class LLMError(Exception):
    """Base class for all LLM-related errors. Catch this in the backend
    if you don't need to distinguish the specific failure type."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when the provider returns a rate-limit / quota error."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when the request times out."""
    pass


class LLMAuthError(LLMError):
    """Raised when the API key is missing or invalid. Retrying will not help."""
    pass


class LLMResponseError(LLMError):
    """Raised when the provider returns an empty or clearly broken response."""
    pass


@dataclass
class LLMResult:
    """
    Standard return object from generate_summary() in both gemini_api.py
    and openai_api.py.

    Using a small object (instead of a bare string) gives the backend and
    Member 3 useful metadata for free, while still being easy to use as
    a plain string via str(result) or result.text.
    """
    text: str          # raw LLM output (expected JSON string, see prompt.py)
    provider: str       # "gemini" or "openai"
    retries_used: int = 0

    def __str__(self):
        return self.text
