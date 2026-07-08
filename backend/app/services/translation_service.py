"""
translation_service.py
------------------------
Single responsibility:
    Input  -> Generated Summary (the dict produced by ai_service.generate_summary()["generated_summary"])
    Output -> Translated Summary

Medical terms (HbA1c, BP, etc.) are kept untranslated where needed --
this is handled inside translation/Translation_Module's hindi.py /
telugu.py prompt builders, not duplicated here.
"""

import logging
from typing import Any, Dict, List

import backend.app.config  # noqa: F401  (sets up sys.path as a side effect)

from translation.translator import translate as translate_text

logger = logging.getLogger(__name__)


def _flatten_summary_text(generated_summary: Dict[str, Any]) -> str:
    """
    Turn the structured generated_summary into one plain-text block for
    the translator, since translation.translator.translate() works on a
    single string (it builds its own prompt around it).
    """
    lines: List[str] = []

    lines.extend(generated_summary.get("summary_bullets", []))

    abnormal_highlights = generated_summary.get("abnormal_highlights", [])
    if abnormal_highlights:
        lines.append("Abnormal findings:")
        lines.extend(abnormal_highlights)

    doctor_notes = generated_summary.get("doctor_notes", {})
    if isinstance(doctor_notes, dict):
        impression = doctor_notes.get("impression")
        if impression:
            lines.append(f"Impression: {impression}")
        recommendations = doctor_notes.get("recommendations", [])
        if recommendations:
            lines.append("Doctor's recommendations:")
            lines.extend(recommendations)

    lifestyle_suggestions = generated_summary.get("lifestyle_suggestions", [])
    if lifestyle_suggestions:
        lines.append("Lifestyle suggestions:")
        lines.extend(lifestyle_suggestions)

    follow_up_advice = generated_summary.get("follow_up_advice", [])
    if follow_up_advice:
        lines.append("Follow-up advice:")
        lines.extend(follow_up_advice)

    return "\n".join(str(line) for line in lines if line)


def translate_summary(generated_summary: Dict[str, Any], language: str) -> Dict[str, Any]:
    """
    Input:  generated_summary -- output of ai_service.generate_summary()["generated_summary"]
            language -- target language ("hindi", "telugu", "tamil", "english", ...)

    Output: Translated Summary --
        {
            "language": "hindi",
            "translated_text": "..."   # full translated block
        }
    """
    source_text = _flatten_summary_text(generated_summary)

    try:
        translated_text = translate_text(source_text, language)
    except Exception as e:
        logger.error("Translation failed for language '%s': %s", language, e)
        translated_text = source_text  # graceful fallback: return original text untranslated

    return {
        "language": language,
        "translated_text": translated_text,
    }
