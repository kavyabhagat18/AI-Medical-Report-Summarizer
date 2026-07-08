# telugu.py

from translation.prompts import TELUGU_PROMPT

def build_telugu_prompt(summary: str) -> str:
    return f"""
{TELUGU_PROMPT}

Medical Report:

{summary}
"""