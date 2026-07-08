import logging
from typing import Optional

# Configure logger
logger = logging.getLogger(__name__)

def format_text(text: Optional[str]) -> str:
    """
    Format cleaned text, removing unnecessary blank lines and extra whitespace.
    Preserves basic report structure and headings.
    
    Args:
        text: Cleaned text to format.
        
    Returns:
        Formatted text.
    """
    if text is None:
        logger.warning("Received None input in format_text.")
        return ""
    
    if not isinstance(text, str):
        logger.warning(f"Received non-string input of type {type(text)} in format_text.")
        text = str(text)

    try:
        # Strip leading/trailing spaces from each line
        lines = [line.strip() for line in text.splitlines()]
        
        # Filter out empty lines
        lines = [line for line in lines if line]
        
        # Join lines back together
        formatted_text = "\n".join(lines)
        return formatted_text
        
    except Exception as e:
        logger.error(f"Unexpected error in format_text: {e}")
        return text