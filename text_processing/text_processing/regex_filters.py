import re
import logging
from typing import Optional

# Configure logger
logger = logging.getLogger(__name__)

# OCR to Digit mapping
OCR_DIGIT_MAP = {
    'O': '0',
    'o': '0',
    'I': '1',
    'l': '1',
    'S': '5',
    'B': '8'
}

def _clean_ocr_digits(s: str) -> str:
    """Helper to replace OCR digit lookalikes with actual digits."""
    if not s:
        return ""
    for ocr_char, digit in OCR_DIGIT_MAP.items():
        s = s.replace(ocr_char, digit)
    return s

def normalize_decorative_elements(text: str) -> str:
    """Remove decorative characters like sequences of stars and dashes."""
    # Remove decorative stars
    text = re.sub(r"\*+", "", text)
    # Remove decorative dashes (3 or more)
    text = re.sub(r"-{3,}", "", text)
    return text

def normalize_dates(text: str) -> str:
    """
    Normalize dates with OCR errors (e.g., 3O/O6/2O26 -> 30/06/2026).
    Supports DD/MM/YYYY and DD-MM-YYYY formats.
    """
    # Pattern matches 1-2 digits/OCR chars, separator / or -, 1-2 digits/OCR chars, separator, 4 digits/OCR chars
    date_pattern = r'\b([0-9OIlSB]{1,2})\s*([/-])\s*([0-9OIlSB]{1,2})\s*\2\s*([0-9OIlSB]{4})\b'
    
    def repl_date(match: re.Match) -> str:
        day = _clean_ocr_digits(match.group(1))
        sep = match.group(2)
        month = _clean_ocr_digits(match.group(3))
        year = _clean_ocr_digits(match.group(4))
        return f"{day}{sep}{month}{sep}{year}"
        
    return re.sub(date_pattern, repl_date, text)

def normalize_ids(text: str) -> str:
    """
    Normalize Report IDs, Patient IDs, and UHIDs (e.g., BT2O261O458 -> BT-2026-10458).
    Supports 2-part and 3-part ID formats.
    """
    # 1. 3-part IDs (e.g., BT-2O26-1O458 or BT2O261O458)
    # Match: 2-4 letters + separator/optional + 4 digit year + separator/optional + 4-8 digits
    three_part_pattern = r'\b([A-Za-z]{2,4})\s*[-]?\s*([0-9OIlSB]{4})\s*[-]?\s*([0-9OIlSB]{4,8})\b'
    
    def repl_three_part(match: re.Match) -> str:
        prefix = match.group(1).upper()
        part2 = _clean_ocr_digits(match.group(2))
        part3 = _clean_ocr_digits(match.group(3))
        return f"{prefix}-{part2}-{part3}"
        
    text = re.sub(three_part_pattern, repl_three_part, text)
    
    # 2. 2-part IDs / UHIDs (e.g., UHID12345O or UHID-12345O)
    # Match: common prefixes (UHID, PID, REG, ID, etc.) or 2-4 uppercase letters, followed by 5-15 digit-like chars
    two_part_pattern = r'\b(UHID|PID|REG|ID|[A-Z]{2,4})\s*[-:]?\s*([0-9OIlSB]{5,15})\b'
    
    def repl_two_part(match: re.Match) -> str:
        prefix = match.group(1).upper()
        digits = _clean_ocr_digits(match.group(2))
        return f"{prefix}-{digits}"
        
    text = re.sub(two_part_pattern, repl_two_part, text, flags=re.IGNORECASE)
    
    return text

def normalize_percentages(text: str) -> str:
    """Normalize percentages with spacing and OCR errors (e.g., 8 . 2 % -> 8.2%)."""
    # Match integer or decimal followed by %
    percentage_pattern = r'\b([0-9OIlSB]+)(?:\s*\.\s*([0-9OIlSB]+))?\s*%'
    
    def repl_percentage(match: re.Match) -> str:
        integer_part = _clean_ocr_digits(match.group(1))
        decimal_part = match.group(2)
        if decimal_part:
            decimal_part = _clean_ocr_digits(decimal_part)
            return f"{integer_part}.{decimal_part}%"
        return f"{integer_part}%"
        
    return re.sub(percentage_pattern, repl_percentage, text)

def normalize_decimals(text: str) -> str:
    """Normalize decimal values with spacing and OCR errors (e.g., 13 . 8 -> 13.8)."""
    # Match sequence of digit-like chars + dot + sequence of digit-like chars
    decimal_pattern = r'\b([0-9OIlSB]+)\s*\.\s*([0-9OIlSB]+)\b'
    
    def repl_decimal(match: re.Match) -> str:
        part1 = _clean_ocr_digits(match.group(1))
        part2 = _clean_ocr_digits(match.group(2))
        return f"{part1}.{part2}"
        
    return re.sub(decimal_pattern, repl_decimal, text)

def normalize_integers(text: str) -> str:
    """Normalize plain integers with OCR mistakes (e.g., 118OO -> 11800)."""
    # Match word consisting only of [0-9OIlSB] containing at least one actual digit [0-9]
    integer_pattern = r'\b(?=[0-9OIlSB]*[0-9])[0-9OIlSB]+\b'
    
    def repl_integer(match: re.Match) -> str:
        return _clean_ocr_digits(match.group(0))
        
    return re.sub(integer_pattern, repl_integer, text)

def normalize_ranges(text: str) -> str:
    """Normalize reference ranges (e.g., 4OOO-11OOO -> 4000 - 11000)."""
    # Match decimal/integer range separated by hyphen
    range_pattern = r'\b([0-9OIlSB]+(?:\.[0-9OIlSB]+)?)\s*-\s*([0-9OIlSB]+(?:\.[0-9OIlSB]+)?)\b'
    
    def repl_range(match: re.Match) -> str:
        part1 = _clean_ocr_digits(match.group(1))
        part2 = _clean_ocr_digits(match.group(2))
        return f"{part1} - {part2}"
        
    return re.sub(range_pattern, repl_range, text)

def normalize_ages(text: str) -> str:
    """Normalize age indicators (e.g., 45Years -> 45 Years)."""
    # Match digits + optional space + age unit
    age_pattern = r'\b([0-9OIlSB]+)\s*(Years|Year|Yrs|Yr|Age)\b'
    
    def repl_age(match: re.Match) -> str:
        num = _clean_ocr_digits(match.group(1))
        unit = match.group(2)
        # Standardize unit to 'Years' if it represents years, or keep it capitalized
        standard_unit = "Years" if unit.lower() in ["years", "year", "yrs", "yr"] else unit
        return f"{num} {standard_unit}"
        
    return re.sub(age_pattern, repl_age, text, flags=re.IGNORECASE)

def normalize_units(text: str) -> str:
    """
    Normalize laboratory units (e.g., mg / dL -> mg/dL).
    Handles spacing and minor spelling errors.
    """
    # 1. Normalize mm Hg -> mmHg (case-insensitive)
    text = re.sub(r"\bmm\s*Hg\b", "mmHg", text, flags=re.IGNORECASE)
    
    # 2. Normalize units with slashes, e.g., mg / dL -> mg/dL, milllon/uL -> million/uL
    unit_pattern = r"\b(mg|ng|g|ug|pg|mmol|umol|u|U|million|milllon|mIU|mEq)\s*/\s*(dL|mL|L|uL|ul|min|hr|d)\b"
    
    def repl_unit(match: re.Match) -> str:
        p1 = match.group(1).lower()
        if p1 == "milllon":
            p1 = "million"
        p2 = match.group(2)
        # Standardize casing of common units
        if p2.lower() == "ul":
            p2 = "uL"
        elif p2.lower() == "dl":
            p2 = "dL"
        elif p2.lower() == "ml":
            p2 = "mL"
        return f"{p1}/{p2}"
        
    text = re.sub(unit_pattern, repl_unit, text, flags=re.IGNORECASE)
    
    # 3. Normalize single slashed units like / uL or /uL
    text = re.sub(
        r"/\s*(uL|ul|mL|dL|L)\b",
        lambda m: f"/{'uL' if m.group(1).lower() == 'ul' else m.group(1)}",
        text,
        flags=re.IGNORECASE
    )
    
    return text

def apply_regex(text: Optional[str]) -> str:
    """
    Main entry point for regex-based cleaning and normalization.
    
    Args:
        text: Cleaned or raw text.
        
    Returns:
        Regex-normalized text.
    """
    if text is None:
        logger.warning("Received None input in apply_regex.")
        return ""
    
    if not isinstance(text, str):
        logger.warning(f"Received non-string input of type {type(text)} in apply_regex.")
        text = str(text)

    try:
        # Step 1: Remove decorative elements (stars, long dashes)
        text = normalize_decorative_elements(text)
        
        # Step 2: Normalize ages (e.g., 45Years -> 45 Years)
        text = normalize_ages(text)
        
        # Step 3: Normalize dates (e.g., 3O/O6/2O26 -> 30/06/2026)
        text = normalize_dates(text)
        
        # Step 4: Normalize ranges (e.g., 4OOO-11OOO -> 4000 - 11000)
        # Run ranges before individual decimals/integers to preserve hyphen separator formatting
        text = normalize_ranges(text)
        
        # Step 5: Normalize Report IDs, Patient IDs, UHIDs (e.g., BT2O261O458 -> BT-2026-10458)
        text = normalize_ids(text)
        
        # Step 6: Normalize percentages (e.g., 8 . 2 % -> 8.2%)
        text = normalize_percentages(text)
        
        # Step 7: Normalize decimal values (e.g., 13 . 8 -> 13.8)
        text = normalize_decimals(text)
        
        # Step 8: Normalize plain integers (e.g., 118OO -> 11800)
        text = normalize_integers(text)
        
        # Step 9: Normalize laboratory units (e.g., mg / dL -> mg/dL)
        text = normalize_units(text)
        
        # Step 10: Fix spacing around colons (e.g., "Age  : 45" -> "Age: 45")
        text = re.sub(r"\s*:\s*", ": ", text)
        
        # Step 11: Remove multiple spaces
        text = re.sub(r"[ ]{2,}", " ", text)
        
        # Step 12: Remove extra blank lines (keep max of 2 consecutive newlines)
        text = re.sub(r"\n{3,}", "\n\n", text)
        
    except Exception as e:
        logger.error(f"Unexpected error in apply_regex: {e}")
        
    return text