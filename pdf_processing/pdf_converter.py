"""
pdf_converter.py

Used ONLY for scanned PDFs. Converts every page of a PDF into a
high-quality image file so it can be handed off to the OCR team's
module. This file performs NO OCR itself.

Uses PyMuPDF (fitz) for rendering, which avoids the external
`poppler` binary dependency required by pdf2image while still
producing high-DPI, high-quality output.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import fitz  # PyMuPDF

from .config import config
from .exceptions import CorruptedPDFError, ImageConversionError, PasswordProtectedPDFError
from .logger import get_logger

logger = get_logger(__name__)


def _build_output_dir(file_path: Path) -> Path:
    """Create a unique subdirectory for this document's converted images."""
    doc_dir = config.temp_image_dir / f"{file_path.stem}_{uuid.uuid4().hex[:8]}"
    doc_dir.mkdir(parents=True, exist_ok=True)
    return doc_dir


def convert_pdf_to_images(file_path: Path) -> list[str]:
    """Convert every page of a scanned PDF into image files.

    Args:
        file_path: Path to the scanned PDF file on disk.

    Returns:
        A list of absolute file paths (as strings) to the generated
        page images, in page order, e.g. ["page1.png", "page2.png"].

    Raises:
        PasswordProtectedPDFError: If the PDF is encrypted.
        CorruptedPDFError: If the PDF cannot be opened.
        ImageConversionError: If image rendering fails.
    """
    image_paths: list[str] = []

    try:
        document = fitz.open(file_path)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to open PDF for image conversion: %s", file_path.name)
        raise CorruptedPDFError(f"Could not open '{file_path.name}' for conversion: {exc}") from exc

    try:
        if document.is_encrypted:
            unlocked = document.authenticate("")
            if not unlocked:
                raise PasswordProtectedPDFError(
                    f"PDF '{file_path.name}' is password-protected and cannot be converted."
                )

        if document.page_count == 0:
            raise ImageConversionError(f"PDF '{file_path.name}' has no pages to convert.")

        output_dir = _build_output_dir(file_path)
        zoom = config.image_dpi / 72  # PDF default is 72 DPI
        matrix = fitz.Matrix(zoom, zoom)
        extension = config.image_format.lower()

        for page_index in range(document.page_count):
            page_number = page_index + 1
            try:
                page = document.load_page(page_index)
                pixmap = page.get_pixmap(matrix=matrix)
                output_path = output_dir / f"page{page_number}.{extension}"
                pixmap.save(str(output_path))
                image_paths.append(str(output_path))
                logger.info("Converted page %d/%d for %s", page_number, document.page_count, file_path.name)
            except Exception as page_exc:  # noqa: BLE001
                logger.error(
                    "Failed to convert page %d of %s: %s", page_number, file_path.name, page_exc
                )
                raise ImageConversionError(
                    f"Failed to convert page {page_number} of '{file_path.name}': {page_exc}"
                ) from page_exc

    finally:
        document.close()

    if not image_paths:
        raise ImageConversionError(f"No images were generated for '{file_path.name}'.")

    return image_paths


def cleanup_temp_images(image_paths: list[str]) -> None:
    """Delete temporary page images after the OCR team has finished with them.

    Failures to delete individual files are logged but do not raise, since
    cleanup is best-effort and should not break the overall pipeline.

    Args:
        image_paths: List of image file paths to remove.
    """
    removed_dirs: set[Path] = set()

    for image_path_str in image_paths:
        image_path = Path(image_path_str)
        try:
            if image_path.exists():
                image_path.unlink()
                removed_dirs.add(image_path.parent)
        except OSError as exc:
            logger.warning("Failed to remove temp image %s: %s", image_path, exc)

    for directory in removed_dirs:
        try:
            if directory.exists() and not any(directory.iterdir()):
                directory.rmdir()
        except OSError as exc:
            logger.warning("Failed to remove temp image directory %s: %s", directory, exc)

    logger.info("Temporary image cleanup complete for %d image(s).", len(image_paths))
