"""
routes/history.py
--------------------
GET /history

Returns a lightweight list of every report ever uploaded/processed,
for the frontend's History page.
"""

import logging

from fastapi import APIRouter

from backend.app.models.response_models import HistoryItem, HistoryResponse
from backend.app.services.db_service import get_all_reports

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/history", response_model=HistoryResponse)
def get_history():
    """List every report in history, most recent first."""
    reports = get_all_reports()
    items = [HistoryItem(**r) for r in reports]
    return HistoryResponse(reports=items, total=len(items))
