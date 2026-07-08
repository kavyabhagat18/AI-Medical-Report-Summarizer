"""
summarizer.py
-------------
Owner: Member 3 (Summary Formatter)

Input:  medical_data (dict) -> the Medical Information Extraction team's
        final JSON, from abnormal_values.build_final_json() (updated schema):

        {
            "patient": {"name": ..., "age": ..., "gender": ...},
            "laboratory_results": [
                {"test_name": ..., "value": ..., "unit": ...,
                 "reference_range": ..., "status": "High"/"Low"/"Normal"/"Unknown"},
                ...
            ],
            "abnormal_summary": {"total_tests": N, "high": N, "low": N,
                                  "normal": N, "unknown": N},
            "doctor_notes": {"impression": str, "recommendations": [str, ...]},
            "data_quality": {"missing_patient_fields": [...],
                              "unknown_status_tests": [...],
                              "doctor_notes_found": bool},
        }

        raw_llm_text (str) -> LLMResult.text from Member 2's gemini_api.py
        / openai_api.py / llm_orchestrator.py (expected to be the JSON
        string described in prompt.RESPONSE_SCHEMA_DESCRIPTION)

Output: final_summary (dict) -> THIS is the object the backend saves to
        the database, the frontend renders on the Summary page, and
        reports/pdf_generator.py + translation/ use to build the PDF.

Because LLMs occasionally don't return perfectly clean JSON (extra
whitespace, stray markdown fences, etc.), this file is defensive about
parsing -- it never crashes the whole pipeline just because the model
added a code fence. It is also defensive about the extraction team's
doctor_notes shape -- their docstring says "impression" is a list[str]
but their actual code returns a plain str, so we normalize either.
"""

import json
import re
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

DISCLAIMER = "This summary is AI-generated and for informational purposes only. Please consult your doctor."

# Keys we always expect back from the LLM (see prompt.RESPONSE_SCHEMA_DESCRIPTION)
EXPECTED_LLM_KEYS = [
    "summary_bullets",
    "abnormal_highlights",
    "diet_suggestions",
    "lifestyle_suggestions",
    "follow_up_advice",
]


def _strip_markdown_fences(text: str) -> str:
    """Some models wrap JSON in ```json ... ``` even when told not to. Strip it."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def parse_llm_response(raw_text: str) -> dict:
    """
    Parses the raw LLM output into a dict with EXPECTED_LLM_KEYS.
    Falls back to empty lists for any missing/unparseable field instead
    of raising, so one bad LLM response doesn't break the whole report.
    """
    cleaned = _strip_markdown_fences(raw_text or "")

    try:
        parsed = json.loads(cleaned)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Failed to parse LLM response as JSON (%s). Falling back to empty sections.", e)
        parsed = {}

    result = {}
    for key in EXPECTED_LLM_KEYS:
        value = parsed.get(key) if isinstance(parsed, dict) else None
        if isinstance(value, list):
            result[key] = [str(item).strip() for item in value if str(item).strip()]
        elif isinstance(value, str) and value.strip():
            # model returned a single string instead of a list -- normalize it
            result[key] = [value.strip()]
        else:
            result[key] = []

    return result


def _abnormal_lab_results(lab_results: list) -> list:
    """Pulls out just the High/Low lab results -- handy for the frontend
    to color-code without re-scanning the full list."""
    if not lab_results:
        return []
    return [r for r in lab_results if r.get("status") in ("High", "Low")]


def _normalize_doctor_notes(doctor_notes) -> dict:
    """
    Normalizes doctor_notes into a consistent {"impression": list[str],
    "recommendations": list[str]} shape.

    Defensive because the extraction team's extract_doctor_notes() docstring
    says "impression" is a list[str], but their actual implementation
    returns a single str (or "" if none found). This handles both cases
    so a future fix on their end doesn't silently break this file.
    """
    if not doctor_notes or not isinstance(doctor_notes, dict):
        return {"impression": [], "recommendations": []}

    impression = doctor_notes.get("impression", [])
    if isinstance(impression, str):
        impression = [impression] if impression.strip() else []
    elif not isinstance(impression, list):
        impression = []

    recommendations = doctor_notes.get("recommendations", [])
    if not isinstance(recommendations, list):
        recommendations = []

    return {
        "impression": [str(i).strip() for i in impression if str(i).strip()],
        "recommendations": [str(r).strip() for r in recommendations if str(r).strip()],
    }


def create_summary(medical_data: dict, raw_llm_text: str, provider: str = "unknown") -> dict:
    """
    Combines the Medical Information Extraction team's structured data
    with the LLM's plain-language output into ONE final object.

    This is the object that should be:
      - saved to backend/database (history.db)
      - returned by the /summarize route
      - rendered on the frontend Summary page
      - passed into reports/pdf_generator.py and translation/translator.py

    Args:
        medical_data: output of abnormal_values.build_final_json()
                      (patient / laboratory_results / abnormal_summary /
                      doctor_notes / data_quality)
        raw_llm_text: raw text from gemini_api / openai_api / llm_orchestrator
        provider: which LLM produced this ("gemini" / "openai"), for logging/debugging

    Returns:
        A single JSON-serializable dict, described in the README.
    """
    medical_data = medical_data or {}
    llm_sections = parse_llm_response(raw_llm_text)
    # ------------------------------------------------------------------
    # Provide fallback recommendations if the LLM returns empty sections.
    # This keeps the summary useful even when the model response is brief.
    # ------------------------------------------------------------------

    if not llm_sections["diet_suggestions"]:
        llm_sections["diet_suggestions"] = [
            "Foods to Eat: Green leafy vegetables, whole grains, fresh fruits, pulses and lean protein.",
            "Foods to Eat: Fibre-rich foods such as oats, beans, lentils and vegetables.",
            "Foods to Avoid: Sugary drinks, processed foods and deep-fried foods.",
            "Foods to Avoid: Reduce excess salt, refined sugar and packaged snacks."
            ]

    if not llm_sections["lifestyle_suggestions"]:
        llm_sections["lifestyle_suggestions"] = [
            "Exercise for at least 30 minutes on most days of the week.",
            "Sleep for 7–8 hours every night.",
            "Drink 2–3 litres of water daily unless advised otherwise by your doctor.",
            "Manage stress through meditation, yoga or deep breathing exercises."
            ]

    if not llm_sections["follow_up_advice"]:
        llm_sections["follow_up_advice"] = [
            "Follow your doctor's advice.",
            "Repeat laboratory tests if recommended.",
            "Seek medical attention if symptoms worsen."
        ]

    patient = medical_data.get("patient", {})
    lab_results = medical_data.get("laboratory_results", [])
    abnormal_summary = medical_data.get("abnormal_summary", {})
    doctor_notes = _normalize_doctor_notes(medical_data.get("doctor_notes"))
    data_quality = medical_data.get("data_quality", {})

    final_summary = {
        "patient": patient,
        "lab_results": lab_results,
        "abnormal_lab_results": _abnormal_lab_results(lab_results),
        "abnormal_summary": abnormal_summary,
        "doctor_notes": doctor_notes,
        "data_quality": data_quality,

        "summary_bullets": (
    llm_sections["summary_bullets"]
    if llm_sections["summary_bullets"]
    else [
        "Your medical report has been analyzed successfully.",
        "Please review the findings below and consult your doctor for medical advice."
    ]
),
        "abnormal_highlights": (
    llm_sections["abnormal_highlights"]
    if llm_sections["abnormal_highlights"]
    else [
        "No significant abnormal findings were identified from the available report."
    ]
),
        "diet_suggestions": llm_sections["diet_suggestions"],
        "lifestyle_suggestions": llm_sections["lifestyle_suggestions"],
        "follow_up_advice": llm_sections["follow_up_advice"],

        "disclaimer": DISCLAIMER,
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "llm_provider": provider,
        },
    }

    return final_summary


if __name__ == "__main__":
    # Manual test -- run `python summarizer.py`
    sample_medical_data = {
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
    fake_llm_response = json.dumps({
        "summary_bullets": ["Your hemoglobin is slightly low.", "Your HbA1c is above the normal range."],
        "abnormal_highlights": ["Low hemoglobin can indicate mild anemia.", "High HbA1c suggests elevated blood sugar over the past 3 months."],
        "diet_suggestions": ["Include iron-rich foods like spinach and legumes.", "Reduce sugar and refined carbohydrate intake."],
        "lifestyle_suggestions": ["Aim for 30 minutes of light exercise daily."],
        "follow_up_advice": ["Repeat blood test in 3 months.", "Discuss HbA1c trend with your doctor."],
    })

    summary = create_summary(sample_medical_data, fake_llm_response, provider="gemini")
    print(json.dumps(summary, indent=2))
