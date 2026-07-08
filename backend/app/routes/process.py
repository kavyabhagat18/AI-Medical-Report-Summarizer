"""
routes/process.py
--------------------
POST /process

Step 2 of the pipeline -- the big one. Given a report_id from a
previous /upload call, this route runs:

    OCR (if needed) -> text_processing (clean/organize) ->
    Medical Information Extraction (patient/labs/notes/flags) ->
    AI Summary (ai_service) -> store final JSON in the database

The resulting report is then available via GET /summary/{report_id},
POST /translate, and POST /generate-pdf.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

import backend.app.config as config
from backend.app.models.request_models import ProcessRequest
from backend.app.models.response_models import ProcessResponse
from backend.app.services.db_service import get_report, save_report
from backend.app.services.ai_service import generate_summary

from pdf_processing.pdf_parser import extract_text as extract_text_from_pdf
from text_processing.regex_filters import apply_regex
from text_processing.clean_text import fix_ocr_errors
from text_processing.formatter import format_text
from medical_information_extraction.patient_details import extract_patient_details
from medical_information_extraction.lab_values import extract_lab_values
from medical_information_extraction.doctor_notes import extract_doctor_notes
from medical_information_extraction.abnormal_values import build_final_json

logger = logging.getLogger(__name__)
router = APIRouter()


def _run_ocr_on_image(image_path: str) -> str:
    """
    Run the OCR pipeline (preprocessing -> Tesseract, EasyOCR as backup)
    on a single image and return the extracted text.

    Falls back gracefully to reading the file as plain text if the OCR
    libraries (pytesseract / easyocr / opencv) aren't available in this
    environment -- this keeps local dev/testing possible without the
    full OCR dependency stack installed.
    """
    try:
        from ocr.image_preprocessing import enhance_medical_image
        from ocr.tesseract_engine import extract_text_via_tesseract

        preprocessed = enhance_medical_image(image_path)
        result = extract_text_via_tesseract(preprocessed)
        text = result.get("text", "")
        confidence = result.get("confidence", 0.0)

        # If Tesseract's confidence is low, try EasyOCR as a backup engine.
        if confidence < 0.5 or not text.strip():
            try:
                from ocr.easyocr_engine import extract_text_from_processed_image
                easyocr_result = extract_text_from_processed_image(preprocessed)
                if easyocr_result.get("text", "").strip():
                    logger.info("Tesseract confidence low (%.2f) -- using EasyOCR result instead.", confidence)
                    text = easyocr_result["text"]
            except Exception as e:
                logger.warning("EasyOCR backup also failed, keeping Tesseract result: %s", e)

        return text

    except Exception as e:
        logger.warning(
            "OCR pipeline unavailable or failed (%s). Falling back to reading '%s' as plain text.",
            e, image_path,
        )
        try:
            return Path(image_path).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""


def _extract_raw_text(file_path: str, pdf_type: str) -> str:
    """Route to the correct extraction path based on the document classification from /upload."""
    if pdf_type == "text":
        return extract_text_from_pdf(Path(file_path))

    if pdf_type == "scanned":
        try:
            from pdf_processing.pdf_converter import convert_pdf_to_images, cleanup_temp_images
            image_paths = convert_pdf_to_images(Path(file_path))
            try:
                page_texts = [_run_ocr_on_image(p) for p in image_paths]
            finally:
                cleanup_temp_images(image_paths)
            return "\n\n".join(page_texts)
        except Exception as e:
            logger.warning("PDF-to-image conversion failed (%s); falling back to direct text extraction.", e)
            return extract_text_from_pdf(Path(file_path))

    if pdf_type == "image":
        return _run_ocr_on_image(file_path)

    if pdf_type == "text_file":
        return Path(file_path).read_text(encoding="utf-8", errors="ignore")

    raise ValueError(f"Unknown pdf_type '{pdf_type}'.")


def _clean_text(raw_text: str) -> str:
    """Run the text_processing team's cleaning chain: regex normalization -> OCR error fixes -> formatting."""
    text = apply_regex(raw_text)
    text = fix_ocr_errors(text)
    text = format_text(text)
    return text


@router.post("/process", response_model=ProcessResponse)
def process_report(request: ProcessRequest):
    """Run OCR, text cleaning, medical extraction, and AI summarization for an uploaded report."""
    report = get_report(request.report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report '{request.report_id}' not found.")

    file_path = report.get("file_path")
    pdf_type = report.get("pdf_type")
    if not file_path or not pdf_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report is missing file_path/pdf_type -- was it uploaded correctly?")

    try:
        raw_text = _extract_raw_text(file_path, pdf_type)
        cleaned_text = _clean_text(raw_text)

        patient = extract_patient_details(cleaned_text)
        laboratory_results = extract_lab_values(cleaned_text)
        doctor_notes = extract_doctor_notes(cleaned_text)

        medical_json = build_final_json(patient, laboratory_results, doctor_notes)

        summary_result = generate_summary(medical_json)

        report.update({
            "patient": medical_json.get("patient", {}),
            "laboratory_results": medical_json.get("laboratory_results", []),
            "doctor_notes": medical_json.get("doctor_notes", {}),
            "ai_summary": summary_result["ai_summary"],
            "generated_summary": summary_result["generated_summary"],
            "diet_recommendations": summary_result["diet_recommendations"],
            "status": "processed",
        })
        save_report(report)

        return ProcessResponse(
            report_id=request.report_id,
            patient=report["patient"],
            laboratory_results=report["laboratory_results"],
            doctor_notes=report["doctor_notes"],
            ai_summary=report["ai_summary"],
            generated_summary=report["generated_summary"],
            diet_recommendations=report["diet_recommendations"],
            success=True,
            message="Report processed successfully.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Processing failed for report %s: %s", request.report_id, e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Processing failed: {str(e)}")
