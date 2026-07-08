"""
routes/summary.py
-------------------
GET    /summary/{report_id}  -- fetch the full stored report
DELETE /summary/{report_id}  -- remove a report from history
"""

import logging

from fastapi import APIRouter, HTTPException, status

from backend.app.models.response_models import DeleteResponse, SummaryResponse
from backend.app.services.db_service import delete_report, get_report

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/summary/{report_id}", response_model=SummaryResponse)
def get_summary(report_id: str):
    """Fetch the full processed report (patient, labs, notes, AI summary, diet, translations, PDF path)."""
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report '{report_id}' not found.")

    return SummaryResponse(
        report_id=report_id,
        patient=report.get("patient", {}),
        laboratory_results=report.get("laboratory_results", []),
        doctor_notes=report.get("doctor_notes", {}),
        ai_summary=report.get("ai_summary", {}),
        generated_summary=report.get("generated_summary", {}),
        diet_recommendations=report.get("diet_recommendations", {}),
        translation=report.get("translation", {}),
        pdf_path=report.get("pdf_path"),
        created_at=report.get("created_at", ""),
    )


@router.delete("/summary/{report_id}", response_model=DeleteResponse)
def delete_summary(report_id: str):
    """Delete a report from history."""
    deleted = delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report '{report_id}' not found.")

    logger.info("Deleted report %s", report_id)
    return DeleteResponse(report_id=report_id, deleted=True, message="Report deleted successfully.")
