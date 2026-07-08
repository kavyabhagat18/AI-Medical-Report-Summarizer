#Extract lab test names, values, units and reference ranges from cleaned report text.

import logging
import re

logger = logging.getLogger(__name__)

LAB_LINE_PATTERN = re.compile(
    r"^(?P<test>[A-Za-z][A-Za-z0-9\s\-/().]{2,40}?)\s*[:\-]?\s*"
    r"(?P<value>\d+\.?\d*)\s*"
    r"(?P<unit>[a-zA-Zµμ%/^0-9]{1,15})?\s*"
    r"\(?\s*(?:Ref(?:erence)?\.?\s*(?:Range|Value)?)?\s*[:\-]?\s*"
    r"(?P<ref_low>\d+\.?\d*)?\s*-\s*(?P<ref_high>\d+\.?\d*)?\)?",
    re.IGNORECASE,
)

# Ignore patient information lines
NON_LAB_PREFIXES = re.compile(
    r"^(Patient\s*Name|Name|Age|Sex|Gender|Date|DOB|Address|Doctor|Hospital|Ref\.?\s*by|Referred\s*by)\b",
    re.IGNORECASE,
)

# Preserve common medical abbreviations
KNOWN_ABBREVIATIONS = {
    "hba1c": "HbA1c",
    "wbc": "WBC",
    "wbc count": "WBC Count",
    "rbc": "RBC",
    "rbc count": "RBC Count",
    "ldl": "LDL",
    "hdl": "HDL",
    "tsh": "TSH",
    "t3": "T3",
    "t4": "T4",
    "crp": "CRP",
    "esr": "ESR",
    "bun": "BUN",
    "alt": "ALT",
    "ast": "AST",
    "mcv": "MCV",
    "mch": "MCH",
    "mchc": "MCHC",
    "pcv": "PCV",
    "plt": "PLT",
    "vldl": "VLDL",
}


def normalize_test_name(raw_name: str) -> str:
    """
    Title-case a test name, but preserve known medical abbreviations
    (HbA1c, WBC, LDL, etc.) that .title() would otherwise mangle.
    """
    cleaned = raw_name.strip()
    lookup_key = cleaned.lower()

    if lookup_key in KNOWN_ABBREVIATIONS:
        return KNOWN_ABBREVIATIONS[lookup_key]

    # Apply title case if abbreviation is unknown
    # appears as a standalone word inside a longer test name
    titled = cleaned.title()
    for abbr_lower, abbr_correct in KNOWN_ABBREVIATIONS.items():
        titled = re.sub(
            rf"\b{re.escape(abbr_lower.title())}\b", abbr_correct, titled
        )
    return titled


def extract_lab_values(text: str) -> list:

    if not text:
        return []

    results = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    for line in lines:
        if NON_LAB_PREFIXES.match(line):
            continue

        match = LAB_LINE_PATTERN.match(line)
        if not match:
            continue

        value_str = match.group("value")
        if not value_str:
            continue

        try:
            value = float(value_str)
        except ValueError:
            continue

        test_name = normalize_test_name(match.group("test"))
        unit = match.group("unit")
        ref_low = match.group("ref_low")
        ref_high = match.group("ref_high")
        reference_range = f"{ref_low}-{ref_high}" if ref_low and ref_high else None

        status="Normal"
        if ref_low and ref_high:
            low=float(ref_low)
            high=float(ref_high)

            if value < low:
                status="Low"
            elif value > high:
                status="High"

        results.append({
            "test_name": test_name,
            "value": value,
            "unit": unit.strip() if unit else None,
            "reference_range": reference_range,
            "status":status
        })

    if not results:
        logger.warning("extract_lab_values() found no lab entries in the given text.")

    return results



