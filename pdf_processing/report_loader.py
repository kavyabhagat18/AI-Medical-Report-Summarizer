"""
report_loader.py

Responsibilities:
    * Validate uploaded file (extension, size, basic signature check).
    * Save uploaded file to disk.
    * Verify the saved file exists and is non-empty.
    * Delegate to the PDF detector to classify the document.

This module is the first stop after a file leaves the FastAPI route
layer and acts as the gatekeeper before any heavier PDF parsing work
is attempted.
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import BinaryIO

from .config import config
from .exceptions import (
    FileNotFoundOnDiskError,
    FileTooLargeError,
    InvalidFileTypeError,
)
from .logger import get_logger
from .pdf_detector import detect_pdf_type

logger = get_logger(__name__)

# The first bytes of a valid PDF file always start with this magic header.
PDF_MAGIC_HEADER = b"%PDF-"


def validate_extension(filename: str) -> None:
    """Ensure the filename has an allowed extension.

    Args:
        filename: Original filename supplied by the client.

    Raises:
        InvalidFileTypeError: If the extension is not allowed.
    """
    suffix = Path(filename).suffix.lower()
    if suffix not in config.allowed_extensions:
        logger.warning("Rejected upload with invalid extension: %s", filename)
        raise InvalidFileTypeError(
            f"Unsupported file extension '{suffix}'. Only PDF files are accepted."
        )


def validate_file_size(size_bytes: int) -> None:
    """Ensure the uploaded file does not exceed the configured size limit.

    Args:
        size_bytes: Size of the uploaded file in bytes.

    Raises:
        FileTooLargeError: If the file exceeds the configured maximum size.
    """
    if size_bytes <= 0:
        raise InvalidFileTypeError("Uploaded file is empty.")

    if size_bytes > config.max_file_size_bytes:
        logger.warning(
            "Rejected upload exceeding size limit: %.2f MB (max %d MB)",
            size_bytes / (1024 * 1024),
            config.max_file_size_mb,
        )
        raise FileTooLargeError(
            f"File size exceeds the maximum allowed size of {config.max_file_size_mb} MB."
        )


def validate_pdf_signature(file_path: Path) -> None:
    """Verify the file actually starts with a PDF magic header.

    This protects against files that merely have a `.pdf` extension but
    are not genuine PDF documents.

    Args:
        file_path: Path to the saved file on disk.

    Raises:
        InvalidFileTypeError: If the file does not start with the PDF signature.
    """
    try:
        with open(file_path, "rb") as f:
            header = f.read(len(PDF_MAGIC_HEADER))
    except OSError as exc:
        raise FileNotFoundOnDiskError(f"Unable to read file for signature check: {exc}") from exc

    if header != PDF_MAGIC_HEADER:
        logger.warning("File failed PDF signature validation: %s", file_path.name)
        raise InvalidFileTypeError("File content does not match a valid PDF signature.")


def save_uploaded_file(file_obj: BinaryIO, original_filename: str) -> Path:
    """Persist an uploaded file-like object to the upload directory.

    A UUID-prefixed filename is used to avoid collisions and to prevent
    directory traversal issues from untrusted filenames.

    Args:
        file_obj: A file-like object opened in binary mode (e.g. SpooledTemporaryFile).
        original_filename: The filename provided by the client.

    Returns:
        Path to the saved file on disk.
    """
    config.ensure_directories()

    safe_name = Path(original_filename).name  # strip any path components
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    destination = config.upload_dir / unique_name

    with open(destination, "wb") as out_file:
        shutil.copyfileobj(file_obj, out_file)

    logger.info("Saved uploaded file to %s", destination)
    return destination


def verify_file_exists(file_path: Path) -> None:
    """Confirm the file exists on disk and is non-empty.

    Args:
        file_path: Path to check.

    Raises:
        FileNotFoundOnDiskError: If the file is missing or empty.
    """
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundOnDiskError(f"File not found on disk: {file_path}")

    if file_path.stat().st_size == 0:
        raise FileNotFoundOnDiskError(f"File on disk is empty: {file_path}")


def load_and_classify(file_obj: BinaryIO, original_filename: str, size_bytes: int) -> dict:
    """High-level entry point: validate, save, and classify an uploaded PDF.

    Args:
        file_obj: A file-like object opened in binary mode.
        original_filename: The filename provided by the client.
        size_bytes: Size of the uploaded file in bytes.

    Returns:
        A dictionary containing the saved file path and detected PDF type, e.g.:
        {"file_path": Path(...), "pdf_type": "text" | "scanned"}
    """
    logger.info("Starting validation for upload: %s", original_filename)

    validate_extension(original_filename)
    validate_file_size(size_bytes)

    saved_path = save_uploaded_file(file_obj, original_filename)
    verify_file_exists(saved_path)
    validate_pdf_signature(saved_path)

    detection_result = detect_pdf_type(saved_path)
    logger.info("Detected PDF type '%s' for %s", detection_result["type"], saved_path.name)

    return {
        "file_path": saved_path,
        "pdf_type": detection_result["type"],
    }
