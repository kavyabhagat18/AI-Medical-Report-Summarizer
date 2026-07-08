"""
openai_api.py
-------------
Owner: Member 2 (LLM Integration)

Same contract as gemini_api.py -- this is what lets the backend swap
providers or use this as a fallback if Gemini fails:

Input:  prompt (str, from Member 1's prompt.build_prompt())
        medical_data (dict, from the Medical Information Extraction team)
Output: LLMResult (see base_llm.py) -- raw text response, expected to be
        the JSON string described in prompt.RESPONSE_SCHEMA_DESCRIPTION.
"""

import os
import time
import logging

from openai import (
    OpenAI,
    RateLimitError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    APIError,
)

from base_llm import (
    LLMResult,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMAuthError,
    LLMResponseError,
    LLMError,
)

logger = logging.getLogger(__name__)

# ---- Config (set these in your .env, loaded via backend/config.py) ----
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 2  # exponential backoff: 2s, 4s, 8s


def _get_client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise LLMAuthError(
            "OPENAI_API_KEY is not set. Add it to your .env file "
            "and load it via backend/config.py before calling this function."
        )
    return OpenAI(api_key=OPENAI_API_KEY)


def generate_summary(prompt: str, medical_data: dict) -> LLMResult:
    """
    Sends the prompt (which already contains the medical data, built by
    prompt.build_prompt) to OpenAI and returns the raw response text.

    Same retry/error behavior as gemini_api.generate_summary(), so the
    backend can call either function interchangeably.
    """
    client = _get_client()

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"},  # matches prompt.py's JSON contract
                timeout=30,
            )

            text = response.choices[0].message.content
            if not text or not text.strip():
                raise LLMResponseError("OpenAI returned an empty response.")

            return LLMResult(
                text=text.strip(),
                provider="openai",
                retries_used=attempt - 1,
            )

        except RateLimitError as e:
            last_error = LLMRateLimitError(f"OpenAI rate limit hit: {e}")
        except APITimeoutError as e:
            last_error = LLMTimeoutError(f"OpenAI request timed out: {e}")
        except AuthenticationError as e:
            # Bad API key -- retrying will not help, fail fast
            raise LLMAuthError(f"OpenAI authentication failed: {e}")
        except BadRequestError as e:
            # Malformed request -- retrying won't help
            raise LLMError(f"OpenAI rejected the request: {e}")
        except LLMResponseError as e:
            last_error = e
        except APIError as e:
            # Catch-all for other transient OpenAI-side errors -- worth retrying
            last_error = LLMError(f"OpenAI API error: {e}")

        if attempt < MAX_RETRIES:
            wait = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                "OpenAI call failed (attempt %d/%d): %s. Retrying in %ds...",
                attempt, MAX_RETRIES, last_error, wait,
            )
            time.sleep(wait)

    raise last_error or LLMError("OpenAI call failed for an unknown reason.")


if __name__ == "__main__":
    # Manual test -- set OPENAI_API_KEY in your environment, then:
    #   python openai_api.py
    from prompt import build_prompt

    sample_data = {
        "patient": {"name": "Ramesh Kumar Sharma", "age": 45, "gender": "Male"},
        "laboratory_results": [
            {"test_name": "Hemoglobin", "value": 10.2, "unit": "g/dL",
             "reference_range": "13.0-17.0", "status": "Low"},
        ],
        "abnormal_summary": {"total_tests": 1, "high": 0, "low": 1, "normal": 0, "unknown": 0},
        "doctor_notes": {"impression": "", "recommendations": ["Patient advised to reduce salt intake."]},
        "data_quality": {"missing_patient_fields": [], "unknown_status_tests": [], "doctor_notes_found": True},
    }
    result = generate_summary(build_prompt(sample_data), sample_data)
    print(f"[{result.provider}, retries={result.retries_used}]\n{result.text}")
