"""
pdf_service.py
----------------
Single responsibility:
    Input  -> Generated Summary (+ patient / laboratory_results, needed
              for the PDF layout, since the template needs more than
              just the summary text)
    Output -> PDF (file path)

reports/pdf_generator.generate_pdf() expects a FLAT dict shape
(patient_name, age, gender, summary, lab_values, recommendations,
diet) -- this module's job is purely to adapt our nested report shape
into that flat shape. No PDF-drawing logic lives here; that's
pdf_generator's job.
"""

import logging
from typing import Any, Dict, List

import backend.app.config  # noqa: F401  (sets up sys.path as a side effect)

from reports.pdf_generator import generate_pdf as _render_pdf

logger = logging.getLogger(__name__)


def _flatten_for_template(
    patient: Dict[str, Any],
    laboratory_results: List[Dict[str, Any]],
    generated_summary: Dict[str, Any],
) -> Dict[str, Any]:
    """Adapt our nested report data into the flat shape pdf_generator's template expects."""
    summary_bullets = generated_summary.get("summary_bullets", [])
    summary_text = " ".join(summary_bullets) if summary_bullets else "No summary available."

    lab_values = [
        {
            "test": entry.get("test_name", ""),
            "value": f"{entry.get('value', '')} {entry.get('unit', '') or ''}".strip(),
            "status": entry.get("status", ""),
        }
        for entry in laboratory_results
    ]

    doctor_notes = generated_summary.get("doctor_notes", {})
    recommendations = []
    if isinstance(doctor_notes, dict):
        recommendations = list(doctor_notes.get("recommendations", []))
    recommendations.extend(generated_summary.get("follow_up_advice", []))

    diet_recommendations = generated_summary.get("diet_recommendations", {})
    diet = list(diet_recommendations.get("include", [])) if isinstance(diet_recommendations, dict) else []

    return {
        "patient_name": patient.get("name") or "Patient",
        "age": patient.get("age") if patient.get("age") is not None else "N/A",
        "gender": patient.get("gender") or "N/A",
        "report_type": "AI Medical Report Summary",
        "summary": summary_text,
        "lab_values": lab_values,
        "recommendations": recommendations,
        "diet": diet,
    }


def generate_pdf(
    patient: Dict[str, Any],
    laboratory_results: List[Dict[str, Any]],
    generated_summary: Dict[str, Any],
) -> str:
    """
    Input:  patient, laboratory_results, generated_summary (output of
            ai_service.generate_summary()["generated_summary"])

    Output: pdf_path (str) -- path to the generated PDF file on disk.
    """
    flat_data = _flatten_for_template(patient, laboratory_results, generated_summary)
    pdf_path = _render_pdf(flat_data)
    logger.info("Generated PDF at %s", pdf_path)
    return str(pdf_path)
