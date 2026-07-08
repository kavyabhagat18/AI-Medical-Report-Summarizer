"""
pdf_reader.py

Low-level text extraction utilities.

    * read_with_pdfplumber() -> primary extraction method
    * read_with_pypdf2()     -> fallback extraction method

Both functions:
    * Read all pages.
    * Ignore empty pages (no extractable text).
    * Preserve original page order.
    * Return a single concatenated text string.
    * Raise domain-specific exceptions on failure rather than leaking
      library-specific exceptions to callers.
"""

from __future__ import annotations

from pathlib import Path

import pdfplumber
import PyPDF2
from PyPDF2.errors import PdfReadError

from .exceptions import (
    CorruptedPDFError,
    PasswordProtectedPDFError,
    TextExtractionError,
)
from .logger import get_logger

logger = get_logger(__name__)

PAGE_SEPARATOR = "\n\n"


def read_with_pdfplumber(file_path: Path) -> str:
    """Extract text from a PDF using pdfplumber.

    Args:
        file_path: Path to the PDF file on disk.

    Returns:
        The concatenated text of all non-empty pages, in original order.

    Raises:
        PasswordProtectedPDFError: If the PDF is encrypted.
        CorruptedPDFError: If the PDF cannot be opened.
        TextExtractionError: If extraction fails for any other reason.
    """
    pages_text: list[str] = []

    try:
        with pdfplumber.open(file_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                try:
                    text = page.extract_text() or ""
                except Exception as page_exc:  # noqa: BLE001
                    logger.warning(
                        "pdfplumber failed to extract page %d of %s: %s",
                        page_number,
                        file_path.name,
                        page_exc,
                    )
                    continue

                stripped = text.strip()
                if stripped:
                    pages_text.append(stripped)
                else:
                    logger.debug("Skipping empty page %d in %s", page_number, file_path.name)

    except Exception as exc:  # noqa: BLE001
        message = str(exc).lower()
        if "password" in message or "encrypt" in message:
            raise PasswordProtectedPDFError(
                f"PDF '{file_path.name}' is password-protected."
            ) from exc
        logger.error("pdfplumber failed to open %s: %s", file_path.name, exc)
        raise CorruptedPDFError(f"pdfplumber could not open '{file_path.name}': {exc}") from exc

    if not pages_text:
        logger.warning("pdfplumber extracted no text from %s", file_path.name)
        raise TextExtractionError(f"pdfplumber extracted no text from '{file_path.name}'.")

    return PAGE_SEPARATOR.join(pages_text)


def read_with_pypdf2(file_path: Path) -> str:
    """Extract text from a PDF using PyPDF2 as a fallback method.

    Args:
        file_path: Path to the PDF file on disk.

    Returns:
        The concatenated text of all non-empty pages, in original order.

    Raises:
        PasswordProtectedPDFError: If the PDF is encrypted and cannot be read.
        CorruptedPDFError: If the PDF cannot be opened.
        TextExtractionError: If extraction fails for any other reason.
    """
    pages_text: list[str] = []

    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)

            if reader.is_encrypted:
                try:
                    # Attempt to open with an empty password; some PDFs are
                    # "encrypted" only for permissions, not viewing.
                    decrypted = reader.decrypt("")
                    if decrypted == 0:
                        raise PasswordProtectedPDFError(
                            f"PDF '{file_path.name}' is password-protected."
                        )
                except PasswordProtectedPDFError:
                    raise
                except Exception as decrypt_exc:  # noqa: BLE001
                    raise PasswordProtectedPDFError(
                        f"PDF '{file_path.name}' is password-protected."
                    ) from decrypt_exc

            for page_number, page in enumerate(reader.pages, start=1):
                try:
                    text = page.extract_text() or ""
                except Exception as page_exc:  # noqa: BLE001
                    logger.warning(
                        "PyPDF2 failed to extract page %d of %s: %s",
                        page_number,
                        file_path.name,
                        page_exc,
                    )
                    continue

                stripped = text.strip()
                if stripped:
                    pages_text.append(stripped)
                else:
                    logger.debug("Skipping empty page %d in %s", page_number, file_path.name)

    except PasswordProtectedPDFError:
        raise
    except PdfReadError as exc:
        logger.error("PyPDF2 failed to read %s: %s", file_path.name, exc)
        raise CorruptedPDFError(f"PyPDF2 could not read '{file_path.name}': {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("Unexpected PyPDF2 failure for %s: %s", file_path.name, exc)
        raise CorruptedPDFError(f"PyPDF2 could not open '{file_path.name}': {exc}") from exc

    if not pages_text:
        logger.warning("PyPDF2 extracted no text from %s", file_path.name)
        raise TextExtractionError(f"PyPDF2 extracted no text from '{file_path.name}'.")

    return PAGE_SEPARATOR.join(pages_text)
