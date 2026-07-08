"""
ai_service.py
--------------
Single responsibility:
    Input  -> Medical JSON (the Medical Information Extraction team's
              output: patient, laboratory_results, doctor_notes,
              abnormal_summary, data_quality)
    Output -> Generated Summary (a dict containing ai_summary,
              diet_recommendations, and the full generated_summary
              package used by translation_service and pdf_service)

This module owns ALL contact with the LLM (Gemini/OpenAI via
ai_summary.llm_orchestrator) and prompt construction. Nothing else in
the backend should call ai_summary.* directly.
"""

import logging
from typing import Any, Dict, List

import backend.app.config  # noqa: F401  (sets up sys.path as a side effect)

from ai_summary.prompt import build_prompt
from ai_summary.llm_orchestrator import get_llm_summary
from ai_summary.summarizer import create_summary
from base_llm import LLMError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------
# Rule-based diet enrichment, layered on top of whatever the LLM
# suggests. This makes diet_recommendations useful even if the LLM's
# own diet_suggestions are generic, by reacting to specific abnormal
# lab flags (e.g. high glucose -> low-glycemic-index foods).
# ---------------------------------------------------------------
_DIET_RULES = [
    (["glucose", "sugar", "hba1c", "diabetic", "insulin"], "High",
     "Low glycemic index foods (green leafy vegetables, whole oats, legumes, lean protein).",
     "Refined sugars, processed sweets, white bread, and sugary drinks."),
    (["cholesterol", "triglyceride", "ldl", "lipid"], "High",
     "Omega-3 sources (walnuts, flaxseeds, fish) and soluble fiber (apples, beans, oats).",
     "Saturated fats, deep-fried food, butter, and processed meats."),
    (["hemoglobin", "iron", "ferritin", "hb"], "Low",
     "Iron-rich foods (spinach, lentils, lean red meat) with Vitamin C to aid absorption.",
     "Tea or coffee immediately with meals, since they can inhibit iron absorption."),
    (["vitamin d", "vit d"], "Low",
     "Vitamin D fortified foods, egg yolks, mushrooms, and moderate sunlight exposure.",
     "Highly processed foods that interfere with calcium/vitamin D absorption."),
    (["uric"], "High",
     "Low-fat dairy, cherries, and high-water-content vegetables.",
     "Red meat, shellfish, and alcoholic beverages."),
    (["creatinine", "bun", "urea"], "High",
     "Low-sodium, controlled-protein vegetables (cauliflower, blueberries, grapes).",
     "Excessive salt, high-potassium foods (bananas, avocados), and high-phosphorus dairy."),
]

_DEFAULT_INCLUDE = [
    "Green leafy vegetables, whole grains, fresh fruits, pulses, and lean protein.",
    "Fibre-rich foods such as oats, beans, lentils, and vegetables.",
]
_DEFAULT_AVOID = [
    "Sugary drinks, processed foods, and deep-fried foods.",
    "Excess salt, refined sugar, and packaged snacks.",
]
_DEFAULT_HYDRATION = "Drink 2-3 litres of water daily unless advised otherwise by your doctor."


def _build_diet_recommendations(laboratory_results: List[Dict[str, Any]], llm_diet_suggestions: List[str]) -> Dict[str, Any]:
    """
    Combine the LLM's own diet suggestions with rule-based additions driven
    by specific abnormal lab flags, in a structured {include, avoid,
    hydration} shape that's easy for the frontend to render.
    """
    include = list(llm_diet_suggestions) if llm_diet_suggestions else []
    avoid: List[str] = []

    for keywords, trigger_status, include_text, avoid_text in _DIET_RULES:
        for entry in laboratory_results:
            test_name = (entry.get("test_name") or "").lower()
            status = entry.get("status", "")
            if any(kw in test_name for kw in keywords) and status == trigger_status:
                if include_text not in include:
                    include.append(include_text)
                if avoid_text not in avoid:
                    avoid.append(avoid_text)
                break

    if not include:
        include = list(_DEFAULT_INCLUDE)
    if not avoid:
        avoid = list(_DEFAULT_AVOID)

    return {
        "include": include,
        "avoid": avoid,
        "hydration": _DEFAULT_HYDRATION,
    }


def generate_summary(medical_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input:  medical_json -- output of
            medical_information_extraction.abnormal_values.build_final_json()
            i.e. {"patient", "laboratory_results", "doctor_notes",
                  "abnormal_summary", "data_quality"}

    Output: Generated Summary -- a dict with three parts:
        {
            "ai_summary": {              # raw LLM-produced content
                "summary_bullets": [...],
                "abnormal_highlights": [...],
                "lifestyle_suggestions": [...],
                "follow_up_advice": [...],
                "disclaimer": "...",
            },
            "diet_recommendations": {    # include / avoid / hydration
                "include": [...], "avoid": [...], "hydration": "..."
            },
            "generated_summary": { ... } # the FULL combined package --
                this is what translation_service and pdf_service expect
                as their input, per the spec.
        }
    """
    prompt = build_prompt(medical_json)

    try:
        llm_result = get_llm_summary(prompt, medical_json)
        raw_llm_text = llm_result.text
        provider = getattr(llm_result, "provider", "unknown")
    except LLMError as e:
        logger.error("Both LLM providers failed to generate a summary: %s", e)
        # Fall back to an empty LLM response -- summarizer.create_summary()
        # already has defensive fallback bullets/diet/lifestyle text built in
        # for exactly this situation, so the pipeline still returns something
        # useful instead of crashing.
        raw_llm_text = "{}"
        provider = "unavailable"

    full_summary = create_summary(medical_json, raw_llm_text, provider=provider)

    laboratory_results = medical_json.get("laboratory_results", [])
    diet_recommendations = _build_diet_recommendations(
        laboratory_results, full_summary.get("diet_suggestions", [])
    )

    ai_summary = {
        "summary_bullets": full_summary.get("summary_bullets", []),
        "abnormal_highlights": full_summary.get("abnormal_highlights", []),
        "lifestyle_suggestions": full_summary.get("lifestyle_suggestions", []),
        "follow_up_advice": full_summary.get("follow_up_advice", []),
        "disclaimer": full_summary.get("disclaimer", ""),
        "meta": full_summary.get("meta", {}),
    }

    # generated_summary is the full package, including diet_recommendations
    # in the shape translation_service/pdf_service will consume.
    generated_summary = dict(full_summary)
    generated_summary["diet_recommendations"] = diet_recommendations

    return {
        "ai_summary": ai_summary,
        "diet_recommendations": diet_recommendations,
        "generated_summary": generated_summary,
    }
