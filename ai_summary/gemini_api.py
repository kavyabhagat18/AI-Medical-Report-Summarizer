"""
gemini_api.py
-------------
Owner: Member 2 (LLM Integration)

Input:  prompt (str, from Member 1's prompt.build_prompt())
        medical_data (dict, from the Medical Information Extraction team)
Output: LLMResult (see base_llm.py) -- raw text response, expected to be
        the JSON string described in prompt.RESPONSE_SCHEMA_DESCRIPTION.

This file's ONLY job is to talk to the Gemini API reliably.
No formatting, no bullet logic, no diet/lifestyle text generation here --
that happens in Member 3's summarizer.py, using whatever this returns.
"""

import os
import time
import logging

import google.generativeai as genai
from google.api_core.exceptions import (
    ResourceExhausted,   # rate limit / quota
    DeadlineExceeded,    # timeout
    Unauthenticated,     # bad API key
    InvalidArgument,     # malformed request
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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 2  # exponential backoff: 2s, 4s, 8s

# Ask Gemini to return raw JSON directly (matches prompt.py's contract).
# This makes summarizer.py's parsing much more reliable than parsing free text.
GENERATION_CONFIG = {
    "response_mime_type": "application/json",
    "temperature": 0.3,  # low temperature -> more consistent, less creative drift
}


def _get_model():
    if not GEMINI_API_KEY:
        raise LLMAuthError(
            "GEMINI_API_KEY is not set. Add it to your .env file "
            "and load it via backend/config.py before calling this function."
        )
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(GEMINI_MODEL, generation_config=GENERATION_CONFIG)


def generate_summary(prompt: str, medical_data: dict) -> LLMResult:
    """
    Sends the prompt (which already contains the medical data, built by
    prompt.build_prompt) to Gemini and returns the raw response text.

    Retries on rate-limit / timeout errors with exponential backoff.
    Raises a specific LLMError subclass on failure so the caller
    (e.g. an orchestrator in the backend) can decide whether to fall
    back to openai_api.generate_summary() instead.
    """
    model = _get_model()

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = model.generate_content(prompt)

            text = getattr(response, "text", None)
            if not text or not text.strip():
                raise LLMResponseError("Gemini returned an empty response.")

            return LLMResult(
                text=text.strip(),
                provider="gemini",
                retries_used=attempt - 1,
            )

        except ResourceExhausted as e:
            last_error = LLMRateLimitError(f"Gemini rate limit hit: {e}")
        except DeadlineExceeded as e:
            last_error = LLMTimeoutError(f"Gemini request timed out: {e}")
        except Unauthenticated as e:
            # Bad API key -- retrying will not help, fail fast
            raise LLMAuthError(f"Gemini authentication failed: {e}")
        except InvalidArgument as e:
            # Malformed request (e.g. bad model name) -- retrying won't help
            raise LLMError(f"Gemini rejected the request: {e}")
        except LLMResponseError as e:
            last_error = e

        if attempt < MAX_RETRIES:
            wait = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                "Gemini call failed (attempt %d/%d): %s. Retrying in %ds...",
                attempt, MAX_RETRIES, last_error, wait,
            )
            time.sleep(wait)

    raise last_error or LLMError("Gemini call failed for an unknown reason.")


if __name__ == "__main__":
    # Manual test -- set GEMINI_API_KEY in your environment, then:
    #   python gemini_api.py
    from prompt import build_prompt

    sample_data = {
        "patient": {"name": "Ramesh Kumar Sharma", "age": 45, "gender": "Male"},
        "laboratory_results": [
            {"test_name": "Hemoglobin", "value": 10.2, "unit": "g/dL",
             "reference_range": "13.0-17.0", "status": "Low"},
            {"test_name": "HbA1c", "value": 6.8, "unit": "%",
             "reference_range": "4.0-5.6", "status": "High"},
        ],
        "abnormal_summary": {"total_tests": 2, "high": 1, "low": 1, "normal": 0, "unknown": 0},
        "doctor_notes": {"impression": "Mild anemia, monitor hemoglobin levels.",
                          "recommendations": ["Patient advised to reduce salt intake."]},
        "data_quality": {"missing_patient_fields": [], "unknown_status_tests": [], "doctor_notes_found": True},
    }
    result = generate_summary(build_prompt(sample_data), sample_data)
    print(f"[{result.provider}, retries={result.retries_used}]\n{result.text}")
