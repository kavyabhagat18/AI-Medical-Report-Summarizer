"""
prompt.py
---------
Owner: Member 1 (Prompt Engineering)

Input:  medical_data (dict) -> the exact JSON produced by the
        Medical Information Extraction team's abnormal_values.build_final_json():

        {
            "patient": {"name": ..., "age": ..., "gender": ...},
            "laboratory_results": [
                {"test_name": ..., "value": ..., "unit": ...,
                 "reference_range": ..., "status": "High"/"Low"/"Normal"/"Unknown"},
                ...
            ],
            "abnormal_summary": {"total_tests": N, "high": N, "low": N,
                                  "normal": N, "unknown": N},
            "doctor_notes": {"impression": "...", "recommendations": ["...", "..."]},
            "data_quality": {"missing_patient_fields": [...],
                              "unknown_status_tests": [...],
                              "doctor_notes_found": true/false}
        }

        NOTE: this function does not hard-code any of these key names --
        it just serializes whatever dict it's given straight into the
        prompt -- so it keeps working even if the extraction team's
        schema changes again. Only the sample data in __main__ below
        needs to be kept in sync for manual testing.

Output: prompt (str) -> ready to send straight into gemini_api.py / openai_api.py

DESIGN DECISION (important for the whole team + deployment):
We instruct the LLM to reply with STRICT JSON in a fixed shape, instead of
free-form bullet text. This is what lets Member 3's summarizer.py parse the
response reliably instead of using fragile regex on prose. If you (Member 1)
change the required output fields, update RESPONSE_SCHEMA_DESCRIPTION below
AND tell Member 3 -- summarizer.py depends on these exact key names.
"""

import json

# ---------------------------------------------------------------------
# Safety instructions -- required on every prompt. Do not remove.
# This is what keeps the tool from sounding like it's diagnosing anyone.
# ---------------------------------------------------------------------
SAFETY_INSTRUCTIONS = """
You are a medical report summarization assistant. Follow these rules strictly:
1. Do NOT diagnose any condition. Only explain what the report shows.
2. Use simple, plain language a non-medical person can understand.
3. Never invent lab values, names, or notes that are not present in the data given.
4. If information is missing (null/empty), do not guess -- omit it or say "not available".
5. Always remind the reader to consult their doctor before making health decisions.
6. Keep tone calm and reassuring, even when values are abnormal.
7. Provide practical and personalized lifestyle recommendations based only on the report findings.
8. Include healthy foods to eat and foods to avoid whenever relevant to the laboratory results.
9. Keep recommendations clear, actionable, and suitable for a general patient.
10. If all results are normal, encourage maintaining a healthy lifestyle instead of creating unnecessary concerns.
"""

# ---------------------------------------------------------------------
# The exact JSON shape we require the LLM to respond with.
# summarizer.py parses these exact keys.
# ---------------------------------------------------------------------
RESPONSE_SCHEMA_DESCRIPTION = """
Respond with ONLY valid JSON (no markdown fences, no extra text before or
after) in exactly this shape:

{
  "summary_bullets": [
    "short plain-language bullet",
    "..."
  ],
  "abnormal_highlights": [
    "simple explanation of each High/Low value",
    "..."
  ],
  "diet_suggestions": [
    "Foods to Eat: ...",
    "Foods to Eat: ...",
    "Foods to Avoid: ...",
    "Foods to Avoid: ..."
  ],
  "lifestyle_suggestions": [
    "Exercise recommendation",
    "Hydration recommendation",
    "Sleep recommendation",
    "Stress management recommendation"
  ],
  "follow_up_advice": [
    "Recommended follow-up test",
    "Consult your doctor for further evaluation"
  ]
}

Rules for the JSON:

- All five keys must always be present.
- Each value must be a list of strings (use [] if nothing applies).
- Do not wrap the JSON in markdown code fences.
- Do not add any text outside the JSON.
- Write in simple patient-friendly English.
- For diet_suggestions, clearly include both "Foods to Eat:" and "Foods to Avoid:" recommendations.
- Give at least 5 practical food recommendations (including Foods to Eat and Foods to Avoid) whenever relevant to the medical findings.
- Do not diagnose diseases.
- Do not invent medical values or recommendations not supported by the report.
"""


def build_prompt(medical_data: dict) -> str:
    """
    Builds the final prompt string sent to the LLM.

    Args:
        medical_data: the structured JSON from the Medical Information
                       Extraction team (patient_details/lab_results/doctor_notes).

    Returns:
        A single prompt string ready for gemini_api.generate_summary()
        or openai_api.generate_summary().
    """
    if not medical_data:
        raise ValueError("build_prompt() requires non-empty medical_data")

    data_str = json.dumps(medical_data, indent=2, ensure_ascii=False)

    prompt = f"""{SAFETY_INSTRUCTIONS}

{RESPONSE_SCHEMA_DESCRIPTION}

Here is the patient's structured medical report data (JSON):

{data_str}

Using ONLY the information provided above:

- Explain the important findings in simple language.
- Highlight abnormal laboratory values and explain them in simple, non-technical language.
- Provide practical diet recommendations with clearly separated Foods to Eat and Foods to Avoid.
- Clearly separate Foods to Eat and Foods to Avoid inside diet_suggestions.
- Include follow-up advice and encourage consultation with a healthcare professional whenever appropriate.
- Do not diagnose diseases.
- Do not invent laboratory values or medical facts.
- Return ONLY valid JSON matching the required schema.
- Keep the response concise, well-structured and easy for patients to understand.

"""
    return prompt.strip()


if __name__ == "__main__":
    # Quick manual check -- run `python prompt.py`
    sample = {
        "patient": {"name": "Ramesh Kumar Sharma", "age": 45, "gender": "Male"},
        "laboratory_results": [
            {"test_name": "Hemoglobin", "value": 10.2, "unit": "g/dL",
             "reference_range": "13.0-17.0", "status": "Low"},
            {"test_name": "HbA1c", "value": 6.8, "unit": "%",
             "reference_range": "4.0-5.6", "status": "High"},
        ],
        "abnormal_summary": {"total_tests": 2, "high": 1, "low": 1, "normal": 0, "unknown": 0},
        "doctor_notes": {"impression": "Mild anemia, monitor hemoglobin levels.",
                          "recommendations": ["Patient advised to reduce salt intake.", "Continue current medication."]},
        "data_quality": {"missing_patient_fields": [], "unknown_status_tests": [], "doctor_notes_found": True},
    }
    print(build_prompt(sample))
