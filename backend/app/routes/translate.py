"""
routes/translate.py
----------------------
POST /translate

Translates a report's generated_summary into the requested language,
caches the result under report["translation"][language] so repeated
requests for the same language don't re-call the translation API.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from backend.app.models.request_models import TranslateRequest
from backend.app.models.response_models import TranslateResponse
from backend.app.services.db_service import get_report, save_report
from backend.app.services.translation_service import translate_summary

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/translate", response_model=TranslateResponse)
def translate_report(request: TranslateRequest):
    """Translate a processed report's summary into the requested language (cached per report+language)."""
    report = get_report(request.report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report '{request.report_id}' not found.")

    if not report.get("generated_summary"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report has not been processed yet -- call POST /process first.",
        )

    language_key = request.language.lower()
    translation_cache = report.get("translation", {})

    if language_key in translation_cache:
        logger.info("Returning cached translation for report %s (%s)", request.report_id, language_key)
        translation_result = translation_cache[language_key]
    else:
        try:
            translation_result = translate_summary(report["generated_summary"], request.language)
        except Exception as e:
            logger.exception("Translation failed for report %s: %s", request.report_id, e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Translation failed: {str(e)}")

        translation_cache[language_key] = translation_result
        report["translation"] = translation_cache
        save_report(report)

    return TranslateResponse(
        report_id=request.report_id,
        language=request.language,
        translation=translation_result,
        success=True,
    )
