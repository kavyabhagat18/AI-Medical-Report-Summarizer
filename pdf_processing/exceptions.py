"""
Custom exception hierarchy for the PDF & Document Processing module.

All exceptions inherit from PDFProcessingError so that calling code
(e.g. pdf_service.py or the FastAPI route layer) can catch a single
base exception when desired, or handle specific failure modes
individually.
"""

from __future__ import annotations


class PDFProcessingError(Exception):
    """Base exception for all PDF processing related errors."""

    def __init__(self, message: str = "An error occurred during PDF processing.") -> None:
        self.message = message
        super().__init__(self.message)


class InvalidFileTypeError(PDFProcessingError):
    """Raised when the uploaded file does not have a valid PDF extension/signature."""

    def __init__(self, message: str = "Uploaded file is not a valid PDF document.") -> None:
        super().__init__(message)


class FileTooLargeError(PDFProcessingError):
    """Raised when the uploaded file exceeds the configured maximum size."""

    def __init__(self, message: str = "Uploaded file exceeds the maximum allowed size.") -> None:
        super().__init__(message)


class FileNotFoundOnDiskError(PDFProcessingError):
    """Raised when an expected file cannot be found on disk."""

    def __init__(self, message: str = "Expected file was not found on disk.") -> None:
        super().__init__(message)


class CorruptedPDFError(PDFProcessingError):
    """Raised when a PDF file is unreadable or structurally corrupted."""

    def __init__(self, message: str = "The PDF file appears to be corrupted or unreadable.") -> None:
        super().__init__(message)


class PasswordProtectedPDFError(PDFProcessingError):
    """Raised when a PDF is encrypted and cannot be opened without a password."""

    def __init__(self, message: str = "The PDF file is password-protected.") -> None:
        super().__init__(message)


class EmptyPDFError(PDFProcessingError):
    """Raised when a PDF contains no pages or no extractable content at all."""

    def __init__(self, message: str = "The PDF file is empty or contains no pages.") -> None:
        super().__init__(message)


class PDFDetectionError(PDFProcessingError):
    """Raised when the text-vs-scanned detection process fails."""

    def __init__(self, message: str = "Failed to determine PDF type (text vs scanned).") -> None:
        super().__init__(message)


class TextExtractionError(PDFProcessingError):
    """Raised when both pdfplumber and PyPDF2 fail to extract text."""

    def __init__(self, message: str = "Failed to extract text from the PDF using all available methods.") -> None:
        super().__init__(message)


class ImageConversionError(PDFProcessingError):
    """Raised when converting scanned PDF pages into images fails."""

    def __init__(self, message: str = "Failed to convert PDF pages into images.") -> None:
        super().__init__(message)


class MissingPagesError(PDFProcessingError):
    """Raised when an unexpected number of pages is encountered during processing."""

    def __init__(self, message: str = "The PDF appears to be missing expected pages.") -> None:
        super().__init__(message)
