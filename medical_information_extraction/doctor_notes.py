# Extract doctor's notes and recommendations, split by header type into
# "impression" (diagnostic conclusions) and "recommendations" (advice /
# follow-up actions), so downstream (ai_summary/prompt.py, summarizer.py,
# backend/app/services/ai_service.py) doesn't have to guess which note is
# which by its position in a list.

import re

IMPRESSION_HEADERS = [
    r"Impression",
    r"Conclusion",
    r"Clinical\s*Notes?",
]

RECOMMENDATION_HEADERS = [
    r"Doctor'?s?\s*Notes?",
    r"Doctor'?s?\s*Recommendations?",
    r"Advice",
    r"Remarks?",
    r"Comments?",
]

ALL_HEADERS = IMPRESSION_HEADERS + RECOMMENDATION_HEADERS

# Stop each block at: another known header, a blank line, or end of string.
# (Without the "another known header" option, if text_processing collapses
# the blank line between sections, one header's block would greedily
# swallow the next section's text too.)
_STOP_LOOKAHEAD = r"(?=\n\s*\n|(?:" + "|".join(ALL_HEADERS) + r")\s*[:\-]|\Z)"

impression_pattern = re.compile(
    r"(?:" + "|".join(IMPRESSION_HEADERS) + r")\s*[:\-]\s*(.+?)" + _STOP_LOOKAHEAD,
    re.IGNORECASE | re.DOTALL,
)

recommendation_pattern = re.compile(
    r"(?:" + "|".join(RECOMMENDATION_HEADERS) + r")\s*[:\-]\s*(.+?)" + _STOP_LOOKAHEAD,
    re.IGNORECASE | re.DOTALL,
)


def _split_block_into_lines(block: str) -> list:
    block = re.sub(r"\s+", " ", block.strip())  # collapse line wraps into single spaces
    lines = re.split(r"(?<=[.])\s+(?=[A-Z])", block)
    return [line.strip(" -\u2022\t") for line in lines if line.strip(" -\u2022\t")]


def extract_doctor_notes(text: str) -> dict:
    """
    Returns:
        {
            "impression": list[str],       # diagnostic impressions/conclusions
            "recommendations": list[str]   # advice / follow-up actions
        }
    """
    impression = []
    recommendations = []

    if text:
        for match in impression_pattern.finditer(text):
            impression.extend(_split_block_into_lines(match.group(1)))

        for match in recommendation_pattern.finditer(text):
            recommendations.extend(_split_block_into_lines(match.group(1)))

    return {
        "impression": impression,
        "recommendations": recommendations,
    }
