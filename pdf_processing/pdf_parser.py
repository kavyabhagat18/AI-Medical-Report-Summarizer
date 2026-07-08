"""
pdf_parser.py

Orchestrates text extraction for text-based PDFs:

    1. Attempt extraction via pdfplumber (read_with_pdfplumber).
    2. If that fails for any reason, fall back to PyPDF2
       (read_with_pypdf2).
    3. If both fail, raise TextExtractionError.

This module is intentionally thin -- the heavy lifting lives in
pdf_reader.py. Keeping the fallback logic separate from the raw
reading functions keeps each file focused on a single responsibility.
"""

from __future__ import annotations

from pathlib import Path

from .exceptions import PDFProcessingError, TextExtractionError
from .logger import get_logger
from .pdf_reader import read_with_pdfplumber, read_with_pypdf2

logger = get_logger(__name__)


def extract_text(file_path: Path) -> str:
    """Extract text from a text-based PDF, with automatic fallback.

    Args:
        file_path: Path to the PDF file on disk.

    Returns:
        The extracted text content of the PDF.

    Raises:
        TextExtractionError: If both pdfplumber and PyPDF2 fail.
        PasswordProtectedPDFError: If the PDF is encrypted (propagated as-is
            since retrying with a different library will not help).
    """
    try:
        logger.info("Attempting extraction with pdfplumber for %s", file_path.name)
        return read_with_pdfplumber(file_path)
    except PDFProcessingError as primary_exc:
        # Password-protection issues won't be solved by switching libraries,
        # but corrupted/empty-extraction issues are worth retrying.
        from .exceptions import PasswordProtectedPDFError

        if isinstance(primary_exc, PasswordProtectedPDFError):
            raise

        logger.warning(
            "pdfplumber extraction failed for %s (%s); falling back to PyPDF2",
            file_path.name,
            primary_exc,
        )

        try:
            return read_with_pypdf2(file_path)
        except PDFProcessingError as fallback_exc:
            logger.error(
                "Both pdfplumber and PyPDF2 failed to extract text from %s", file_path.name
            )
            raise TextExtractionError(
                f"Failed to extract text from '{file_path.name}' using all available methods: "
                f"pdfplumber error='{primary_exc}', PyPDF2 error='{fallback_exc}'"
            ) from fallback_exc
