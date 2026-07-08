# ai_summary/ — AI Summarization & Prompt Engineering

Owned by: Member 1 (prompt.py), Member 2 (gemini_api.py, openai_api.py,
base_llm.py, llm_orchestrator.py), Member 3 (summarizer.py)

## What this module does

Takes the structured JSON produced by the **Medical Information Extraction**
team and turns it into a plain-language, patient-friendly summary with diet,
lifestyle, and follow-up suggestions.

## Input (from Medical Information Extraction team)

This module expects the exact output of `abnormal_values.build_final_json()`
(**updated / final schema**):

```json
{
  "patient": {"name": "...", "age": 45, "gender": "Male"},
  "laboratory_results": [
    {"test_name": "Hemoglobin", "value": 10.2, "unit": "g/dL",
     "reference_range": "13.0-17.0", "status": "Low"}
  ],
  "abnormal_summary": {"total_tests": 4, "high": 2, "low": 1, "normal": 1, "unknown": 0},
  "doctor_notes": {"impression": "Mild anemia, monitor hemoglobin levels.",
                    "recommendations": ["Patient advised to reduce salt intake."]},
  "data_quality": {"missing_patient_fields": [], "unknown_status_tests": [], "doctor_notes_found": true}
}
```

**Heads up on `doctor_notes.impression`:** the extraction team's own
docstring says this should be a `list[str]`, but their current code
actually returns a plain `str` (or `""` if nothing found). `summarizer.py`
normalizes either shape defensively, so this module keeps working even
if that gets "corrected" on their end later.

## How the backend team should call this module

```python
from ai_summary.prompt import build_prompt
from ai_summary.llm_orchestrator import get_llm_summary
from ai_summary.summarizer import create_summary

# medical_data comes from the Medical Information Extraction team
prompt = build_prompt(medical_data)
llm_result = get_llm_summary(prompt, medical_data)   # tries Gemini, falls back to OpenAI
final_summary = create_summary(medical_data, llm_result.text, provider=llm_result.provider)

# final_summary is now ready to:
#   - save to backend/database (history.db)
#   - return from the /summarize route
#   - render on the frontend Summary page
#   - pass into reports/pdf_generator.py and translation/translator.py
```

Only 3 function calls needed. Error handling and retries are already
built in — `get_llm_summary()` raises `base_llm.LLMError` (or a subclass)
only if BOTH Gemini and OpenAI fail.

## Output (what the rest of the app receives)

```json
{
  "patient": {...},
  "lab_results": [...],
  "abnormal_lab_results": [...],
  "abnormal_summary": {"total_tests": 4, "high": 2, "low": 1, "normal": 1, "unknown": 0},
  "doctor_notes": {"impression": [...], "recommendations": [...]},
  "data_quality": {...},
  "summary_bullets": ["...", "..."],
  "abnormal_highlights": ["...", "..."],
  "diet_suggestions": ["...", "..."],
  "lifestyle_suggestions": ["...", "..."],
  "follow_up_advice": ["...", "..."],
  "disclaimer": "This summary is AI-generated ... consult your doctor.",
  "meta": {"generated_at": "...", "llm_provider": "gemini"}
}
```

Note: in the output, `doctor_notes.impression` is always normalized to a
`list[str]` (even though the extraction team currently sends a single
string) so the frontend/PDF team can treat it the same way as
`recommendations` — no special-casing needed on their side.

This is a flat, JSON-serializable dict — safe to store directly in the
database and to hand to the frontend/PDF/translation teams unchanged.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in your real API keys
```

## Files

| File | Owner | Role |
|---|---|---|
| `prompt.py` | Member 1 | Builds the prompt string, enforces JSON-only response format |
| `base_llm.py` | Member 2 | Shared exceptions + `LLMResult` interface |
| `gemini_api.py` | Member 2 | Gemini integration, retries, error handling |
| `openai_api.py` | Member 2 | OpenAI integration (same interface as Gemini) |
| `llm_orchestrator.py` | Member 2 | Single entry point: tries Gemini, falls back to OpenAI |
| `summarizer.py` | Member 3 | Parses LLM JSON, merges with extraction data, builds final summary |

## Testing without API keys

Run `demo_full_pipeline.py` (in `/integration_test` alongside a copy of
the Medical Information Extraction team's files) — it runs the entire
pipeline with a mocked LLM response, so anyone can verify the wiring
before real API keys are configured.

## Why the LLM is asked for strict JSON

`prompt.py` instructs the model to return JSON with fixed keys
(`summary_bullets`, `abnormal_highlights`, `diet_suggestions`,
`lifestyle_suggestions`, `follow_up_advice`) instead of free-form bullet
text. This is what lets `summarizer.py` parse the response reliably
instead of relying on fragile regex over prose. If the LLM ever returns
malformed JSON, `summarizer.py` falls back to empty lists for the
affected fields rather than crashing the pipeline.
