import logging
import unicodedata
import re
from typing import Optional

# Configure logger
logger = logging.getLogger(__name__)

def normalize_unicode(text: str) -> str:
    """Normalize Unicode characters to compatibility form KC (NFKC)."""
    try:
        normalized = unicodedata.normalize("NFKC", text)
        return normalized
    except Exception as e:
        logger.error(f"Error normalizing Unicode characters: {e}")
        # Fallback to returning original text if normalization fails
        return text

def remove_extra_whitespace(text: str) -> str:
    """Remove extra spaces within lines while preserving line structure."""
    if not text:
        return text
    # Replace multiple spaces with a single space, but keep newlines intact
    lines = []
    for line in text.splitlines():
        # Remove consecutive spaces but keep single space
        cleaned_line = re.sub(r"[ ]{2,}", " ", line)
        lines.append(cleaned_line)
    return "\n".join(lines)

def fix_common_ocr_words(text: str) -> str:
    """Fix common OCR word mistakes using generic case-preserving rules."""
    if not text:
        return text

    # Standardize HbA1c first since it has mixed casing
    text = re.sub(
        r'\bhba[1il]c\b',
        lambda m: "HBA1C" if m.group(0).isupper() else "HbA1c",
        text,
        flags=re.IGNORECASE
    )

    # Standardize Patient ID
    text = re.sub(
        r'\bpatient\s+l[dD]\b',
        lambda m: "PATIENT ID" if m.group(0).isupper() else "Patient ID",
        text,
        flags=re.IGNORECASE
    )

    # Standardize END OF REPORT
    text = re.sub(
        r'\bend\s+[0o]f\s+rep[0o]rt\b',
        lambda m: "END OF REPORT" if m.group(0).isupper() else "End of Report",
        text,
        flags=re.IGNORECASE
    )

    # Mapping of lowercase misspelled words to their lowercase correct spellings
    corrections = {
        r'\bpatlent\b': 'patient',
        r'\bdiagnostlcs\b': 'diagnostics',
        r'\blaborat[0o]ry\b': 'laboratory',
        r'\breferrlng\b': 'referring',
        r'\bcollectl[o0]n\b': 'collection',
        r'\bbl[0o]{2}d\b': 'blood',
        r'\bc[0o]unt\b': 'count',
        r'\bc[0o]mplete\b': 'complete',
        r'\bhemoglobln\b': 'hemoglobin',
        r'\bmill[o0]n\b': 'million',
        r'\bfastlng\b': 'fasting',
        r'\bprandlal\b': 'prandial',
        r'\bcreatlnlne\b': 'creatinine',
        r'\bvlta?min\b': 'vitamin',
        r'\bblllrubln\b': 'bilirubin',
        r'\btriglycerldes\b': 'triglycerides',
        r'\bproflle\b': 'profile',
        r'\bfunctl[o0]n\b': 'function',
        r'\bllver\b': 'liver',
        r'\bllpld\b': 'lipid',
        r'\bkldney\b': 'kidney',
        r'\bdeflclency\b': 'deficiency',
        r'\brecommendatl[o0]ns\b': 'recommendations',
        r'\bexerclse\b': 'exercise',
        r'\bdlabetes\b': 'diabetes',
        r'\brep[0o]rt\b': 'report',
        r'\b[0o]f\b': 'of'
    }

    def get_case_preserved_replacement(repl: str):
        def repl_func(match: re.Match) -> str:
            word = match.group(0)
            if word.isupper():
                return repl.upper()
            if word[0].isupper() if word else False:
                return repl.capitalize()
            if word.islower():
                return repl.lower()
            return repl
        return repl_func

    try:
        for pattern, repl in corrections.items():
            text = re.sub(
                pattern,
                get_case_preserved_replacement(repl),
                text,
                flags=re.IGNORECASE
            )
    except Exception as e:
        logger.error(f"Error applying OCR word corrections: {e}")

    return text

def fix_ocr_errors(text: Optional[str]) -> str:
    """
    Main entry point for fixing OCR word mistakes, normalizing whitespace and Unicode.
    
    Args:
        text: Raw OCR text to clean.
        
    Returns:
        Cleaned and normalized text.
    """
    if text is None:
        logger.warning("Received None input in fix_ocr_errors.")
        return ""
    
    if not isinstance(text, str):
        logger.warning(f"Received non-string input of type {type(text)} in fix_ocr_errors.")
        text = str(text)

    try:
        # Normalize Unicode characters
        text = normalize_unicode(text)
        
        # Remove extra whitespace
        text = remove_extra_whitespace(text)
        
        # Fix common OCR word errors
        text = fix_common_ocr_words(text)
        
    except Exception as e:
        logger.error(f"Unexpected error in fix_ocr_errors pipeline: {e}")
        
    return text