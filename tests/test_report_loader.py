"""
tests/test_report_loader.py

Unit tests for validation logic in report_loader.py.
These tests do not require real PDF files for the validation-only checks.
"""

import io
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))

from pdf_processing import report_loader  # noqa: E402
from pdf_processing.exceptions import FileTooLargeError, InvalidFileTypeError  # noqa: E402


def test_validate_extension_accepts_pdf():
    report_loader.validate_extension("report.pdf")  # should not raise


def test_validate_extension_rejects_non_pdf():
    with pytest.raises(InvalidFileTypeError):
        report_loader.validate_extension("report.docx")


def test_validate_file_size_rejects_zero_bytes():
    with pytest.raises(InvalidFileTypeError):
        report_loader.validate_file_size(0)


def test_validate_file_size_rejects_oversized_file():
    too_large = report_loader.config.max_file_size_bytes + 1
    with pytest.raises(FileTooLargeError):
        report_loader.validate_file_size(too_large)


def test_validate_file_size_accepts_valid_size():
    report_loader.validate_file_size(1024)  # should not raise


def test_save_and_verify_uploaded_file(tmp_path, monkeypatch):
    import dataclasses

    patched_config = dataclasses.replace(report_loader.config, upload_dir=tmp_path)
    monkeypatch.setattr(report_loader, "config", patched_config)

    fake_pdf_bytes = b"%PDF-1.4 fake content"
    file_obj = io.BytesIO(fake_pdf_bytes)

    saved_path = report_loader.save_uploaded_file(file_obj, "sample.pdf")

    assert saved_path.exists()
    report_loader.verify_file_exists(saved_path)  # should not raise
    report_loader.validate_pdf_signature(saved_path)  # should not raise
