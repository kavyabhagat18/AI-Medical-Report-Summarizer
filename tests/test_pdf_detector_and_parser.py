"""
tests/test_pdf_detector_and_parser.py

Unit tests for pdf_detector.py and pdf_parser.py using a small,
programmatically generated text-based PDF (via PyMuPDF) so the tests
have no external file dependencies.
"""

import sys
from pathlib import Path

import fitz  # PyMuPDF
import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))

from pdf_processing import pdf_detector, pdf_parser  # noqa: E402
from pdf_processing.exceptions import EmptyPDFError  # noqa: E402


@pytest.fixture
def text_pdf(tmp_path) -> Path:
    """Create a minimal text-based PDF for testing."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Patient Name: John Doe\nDiagnosis: Routine checkup, no issues found.")
    output_path = tmp_path / "sample_text.pdf"
    doc.save(output_path)
    doc.close()
    return output_path


@pytest.fixture
def empty_pdf(tmp_path) -> Path:
    """Create a PDF with zero pages for testing edge cases.

    PyMuPDF refuses to save documents with zero pages, so we hand-craft
    a minimal valid PDF structure with an empty /Kids array instead.
    """
    content = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\n"
        b"trailer<</Root 1 0 R>>\n"
        b"%%EOF"
    )
    output_path = tmp_path / "empty.pdf"
    output_path.write_bytes(content)
    return output_path


def test_detect_pdf_type_returns_text_for_text_pdf(text_pdf):
    result = pdf_detector.detect_pdf_type(text_pdf)
    assert result == {"type": "text"}


def test_detect_pdf_type_raises_for_empty_pdf(empty_pdf):
    with pytest.raises(EmptyPDFError):
        pdf_detector.detect_pdf_type(empty_pdf)


def test_extract_text_returns_expected_content(text_pdf):
    text = pdf_parser.extract_text(text_pdf)
    assert "John Doe" in text
    assert "Routine checkup" in text
