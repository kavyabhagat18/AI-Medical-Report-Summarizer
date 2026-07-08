"""
pdf_detector.py

Determines whether a PDF is:
    * "text"    -> contains selectable/extractable text
    * "scanned" -> contains only images / no extractable text

Detection strategy:
    Open the PDF with pdfplumber and inspect the first N pages
    (configurable via config.detection_pages_to_check). If the combined
    extracted text exceeds a minimum character threshold, the PDF is
    classified as text-based. Otherwise it is classified as scanned.

Also handles password-protected and corrupted PDFs by raising the
appropriate custom exceptions so callers can return clean error
responses instead of crashing.
"""

from __future__ import annotations

from pathlib import Path

import pdfplumber
from pdfplumber.utils.exceptions import PdfminerException

from .config import config
from .exceptions import (
    CorruptedPDFError,
    EmptyPDFError,
    PasswordProtectedPDFError,
    PDFDetectionError,
)
from .logger import get_logger

logger = get_logger(__name__)


def _is_encrypted(pdf: "pdfplumber.PDF") -> bool:
    """Check whether the underlying PDF document is encrypted."""
    try:
        return bool(getattr(pdf.doc, "is_extractable", True) is False)
    except AttributeError:
        return False


def detect_pdf_type(file_path: Path) -> dict:
    """Classify a PDF as text-based or scanned.

    Args:
        file_path: Path to the PDF file on disk.

    Returns:
        A dictionary in the form {"type": "text"} or {"type": "scanned"}.

    Raises:
        PasswordProtectedPDFError: If the PDF requires a password to open.
        CorruptedPDFError: If the PDF cannot be opened/parsed at all.
        EmptyPDFError: If the PDF has zero pages.
        PDFDetectionError: For any other unexpected detection failure.
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)

            if total_pages == 0:
                raise EmptyPDFError(f"PDF '{file_path.name}' contains zero pages.")

            pages_to_check = min(config.detection_pages_to_check, total_pages)
            extracted_chars = 0

            for index in range(pages_to_check):
                page = pdf.pages[index]
                page_text = page.extract_text() or ""
                extracted_chars += len(page_text.strip())

            if extracted_chars >= config.min_chars_for_text_pdf:
                return {"type": "text"}

            return {"type": "scanned"}

    except PasswordProtectedPDFError:
        raise
    except EmptyPDFError:
        raise
    except (PdfminerException, ValueError) as exc:
        message = str(exc).lower()
        if "password" in message or "encrypt" in message:
            logger.warning("Password-protected PDF detected: %s", file_path.name)
            raise PasswordProtectedPDFError(
                f"PDF '{file_path.name}' is password-protected and cannot be processed."
            ) from exc
        logger.error("Corrupted PDF detected during type detection: %s", file_path.name)
        raise CorruptedPDFError(f"PDF '{file_path.name}' could not be parsed: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - we want to convert any failure into a domain error
        message = str(exc).lower()
        if "password" in message or "encrypt" in message:
            logger.warning("Password-protected PDF detected: %s", file_path.name)
            raise PasswordProtectedPDFError(
                f"PDF '{file_path.name}' is password-protected and cannot be processed."
            ) from exc
        logger.error("Unexpected error during PDF detection for %s: %s", file_path.name, exc)
        raise PDFDetectionError(f"Failed to detect PDF type for '{file_path.name}': {exc}") from exc
