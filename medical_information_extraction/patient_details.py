#Extract patient details such as name, age and gender from cleaned medical report text.

import re


def extract_patient_details(text: str) -> dict:

    if not text:
        return {"name": None, "age": None, "gender": None}

    return {
        "name":extract_name(text),
        "age":extract_age(text),
        "gender":extract_gender(text),
    }


def extract_name(text: str):
    pattern = r"(?:Patient\s*Name|Name\s*of\s*Patient|Name)\s*[:\-]\s*([A-Za-z.\s]{2,40})"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        # cut off if the next field (Age/Sex/etc.) bled into the same line
        name = re.split(r"\b(Age|Sex|Gender|Date|DOB)\b", name, flags=re.IGNORECASE)[0]
        return name.strip().title()
    return None


def extract_age(text: str):
    patterns = [
        r"Age\s*[:\-]?\s*(\d{1,3})\s*(?:Y|Yrs|Years)?",
        r"(\d{1,3})\s*(?:Y|Yrs|Years)\s*/\s*(?:M|F|Male|Female)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue
    return None


def extract_gender(text: str):
    match = re.search(r"(?:Sex|Gender)\s*[:\-]?\s*(Male|Female|M|F)\b", text, re.IGNORECASE)
    if match:
        g = match.group(1).upper()
        if g in ("M", "MALE"):
            return "Male"
        if g in ("F", "FEMALE"):
            return "Female"
    return None


def extract_date(text:str):
    patterns=[
        r"(?:Date|Report\s*Date|DOB)\s*[:\-]?\s*([\d]{1,2}[/-][\d]{2,4})"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            return match.group(1)

    return None