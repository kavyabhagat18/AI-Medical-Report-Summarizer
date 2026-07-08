"""
Centralized configuration for the PDF & Document Processing module.

Values can be overridden via environment variables so the module
behaves consistently across local development, CI, and production
without code changes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class PDFProcessingConfig:
    """Immutable configuration object for PDF processing."""

    # Directories
    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    upload_dir: Path = field(default_factory=lambda: Path(
        os.getenv("UPLOAD_DIR", str(Path(__file__).resolve().parent.parent / "uploads"))
    ))
    temp_image_dir: Path = field(default_factory=lambda: Path(
        os.getenv(
            "TEMP_IMAGE_DIR",
            str(Path(__file__).resolve().parent.parent / "uploads" / "temp_images"),
        )
    ))

    # File validation
    allowed_extensions: tuple[str, ...] = (".pdf",)
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "25"))

    # Detection
    detection_pages_to_check: int = int(os.getenv("DETECTION_PAGES_TO_CHECK", "3"))
    min_chars_for_text_pdf: int = int(os.getenv("MIN_CHARS_FOR_TEXT_PDF", "20"))

    # Image conversion
    image_dpi: int = int(os.getenv("IMAGE_DPI", "300"))
    image_format: str = os.getenv("IMAGE_FORMAT", "PNG")

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    def ensure_directories(self) -> None:
        """Create required directories if they do not already exist."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.temp_image_dir.mkdir(parents=True, exist_ok=True)


config = PDFProcessingConfig()
config.ensure_directories()
