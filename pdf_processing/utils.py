"""
utils.py

Reusable helper functions shared across the PDF processing module,
including bonus metadata extraction.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pdfplumber

from .exceptions import CorruptedPDFError, PasswordProtectedPDFError
from .logger import get_logger

logger = get_logger(__name__)


def extract_pdf_metadata(file_path: Path) -> dict[str, Any]:
    """Extract basic metadata from a PDF file.

    Args:
        file_path: Path to the PDF file on disk.

    Returns:
        A dictionary with keys: author, title, creation_date, page_count.
        Missing metadata fields default to None.

    Raises:
        PasswordProtectedPDFError: If the PDF is encrypted.
        CorruptedPDFError: If the PDF cannot be opened.
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            metadata = pdf.metadata or {}
            return {
                "author": metadata.get("Author"),
                "title": metadata.get("Title"),
                "creation_date": metadata.get("CreationDate"),
                "page_count": len(pdf.pages),
            }
    except Exception as exc:  # noqa: BLE001
        message = str(exc).lower()
        if "password" in message or "encrypt" in message:
            raise PasswordProtectedPDFError(
                f"PDF '{file_path.name}' is password-protected."
            ) from exc
        logger.error("Failed to extract metadata from %s: %s", file_path.name, exc)
        raise CorruptedPDFError(f"Could not extract metadata from '{file_path.name}': {exc}") from exc


def get_page_count(file_path: Path) -> int:
    """Return the total number of pages in a PDF.

    Args:
        file_path: Path to the PDF file on disk.

    Returns:
        The number of pages.
    """
    metadata = extract_pdf_metadata(file_path)
    return metadata["page_count"]


def format_file_size(size_bytes: int) -> str:
    """Return a human-readable string for a byte size, e.g. '2.35 MB'."""
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"
