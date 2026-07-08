"""
routes/download.py
---------------------
POST /generate-pdf

Generates a downloadable PDF for a processed report, caches the
resulting pdf_path on the report so repeated calls don't regenerate
the file unnecessarily.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from backend.app.models.request_models import GeneratePDFRequest
from backend.app.models.response_models import GeneratePDFResponse
from backend.app.services.db_service import get_report, save_report
from backend.app.services.pdf_service import generate_pdf as build_pdf

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate-pdf", response_model=GeneratePDFResponse)
def generate_pdf_route(request: GeneratePDFRequest):
    """Generate (or return a cached) downloadable PDF summary for a processed report."""
    report = get_report(request.report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report '{request.report_id}' not found.")

    if not report.get("generated_summary"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report has not been processed yet -- call POST /process first.",
        )

    if report.get("pdf_path"):
        logger.info("Returning cached PDF for report %s", request.report_id)
        return GeneratePDFResponse(report_id=request.report_id, pdf_path=report["pdf_path"], success=True)

    try:
        pdf_path = build_pdf(
            patient=report.get("patient", {}),
            laboratory_results=report.get("laboratory_results", []),
            generated_summary=report["generated_summary"],
        )
    except Exception as e:
        logger.exception("PDF generation failed for report %s: %s", request.report_id, e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PDF generation failed: {str(e)}")

    report["pdf_path"] = pdf_path
    save_report(report)

    return GeneratePDFResponse(report_id=request.report_id, pdf_path=pdf_path, success=True)
