#Detect abnormal lab values and generate the final structured JSON

from typing import List, Dict, Optional, Tuple


def parse_reference_range(range_str: Optional[str]) -> Optional[Tuple[float, float]]:
    """
    Convert a reference range string like "70-110" into a (low, high) tuple.
    Returns None if the range is missing or malformed.
    """
    if not range_str:
        return None
    try:
        low_str, high_str = range_str.split("-")
        return float(low_str.strip()), float(high_str.strip())
    except (ValueError, AttributeError):
        return None


def check_status(value: float, reference_range: Optional[str]) -> str:
    """
    Compare a single lab value to its reference range.
    Returns:
        "High" | "Low" | "Normal" | "Unknown"
    """
    bounds = parse_reference_range(reference_range)
    if bounds is None or value is None:
        return "Unknown"

    low, high = bounds
    if value < low:
        return "Low"
    if value > high:
        return "High"
    return "Normal"


def detect_abnormal_values(lab_values: List[Dict]) -> List[Dict]:
    
    #Add the status (High, Low, Normal or Unknown) to each lab result
    

    updated_results = []
    for entry in lab_values:
        status = check_status(entry.get("value"), entry.get("reference_range"))
        updated_entry = dict(entry)
        updated_entry["status"] = status
        updated_results.append(updated_entry)
    return updated_results


def build_final_json(
    patient: Dict,
    lab_values: List[Dict],
    doctor_notes: Dict,
) -> Dict:
    
    # Combine patient details, lab results and doctor notes into a nested JSON
    processed_results = detect_abnormal_values(lab_values)

    abnormal_summary = {"total_tests": len(processed_results), "high": 0, "low": 0, "normal": 0, "unknown": 0}
    for entry in processed_results:
        key = entry["status"].lower()
        if key in abnormal_summary:
            abnormal_summary[key] += 1

    doctor_notes = doctor_notes or {}
    notes_found = bool(doctor_notes.get("impression")) or bool(doctor_notes.get("recommendations"))

    data_quality = {
        "missing_patient_fields": [k for k, v in (patient or {}).items() if v is None],
        "unknown_status_tests": [e["test_name"] for e in processed_results if e["status"] == "Unknown"],
        "doctor_notes_found": notes_found,
    }

    return {
        "patient": patient,
        "laboratory_results": processed_results,
        "abnormal_summary": abnormal_summary,
        "doctor_notes": doctor_notes,
        "data_quality": data_quality,
    }


