# hindi.py

from translation.prompts import HINDI_PROMPT

def build_hindi_prompt(summary: str) -> str:
    return f"""
{HINDI_PROMPT}

Medical Report:

{summary}
"""