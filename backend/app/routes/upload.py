"""
routes/upload.py
------------------
POST /upload

Step 1 of the pipeline: accept a report file (PDF, image, or TXT),
save it to disk, classify it (text-based PDF vs scanned), and create
an initial report_id entry in the database. Does NOT run OCR or
extraction yet -- that happens in POST /process.
"""

import logging
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

import backend.app.config as config
from backend.app.models.response_models import UploadResponse
from backend.app.services.db_service import save_report

from pdf_processing.report_loader import load_and_classify

logger = logging.getLogger(__name__)
router = APIRouter()


class _FileLikeWrapper:
    """Adapts FastAPI's UploadFile into the plain read/seek interface load_and_classify() expects."""
    def __init__(self, upload_file: UploadFile):
        self.upload_file = upload_file

    def read(self, size: int = -1):
        return self.upload_file.file.read(size)

    def seek(self, offset: int, whence: int = 0):
        self.upload_file.file.seek(offset, whence)


def _save_generic_file(file: UploadFile) -> Path:
    """Save a non-PDF file (image or txt) to the uploads directory with a unique name."""
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    destination = config.UPLOAD_DIR / unique_name
    with open(destination, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return destination


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload a medical report (PDF, PNG, JPG, or TXT) and classify it."""
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in config.ALLOWED_UPLOAD_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{suffix}'. Allowed formats: PDF, PNG, JPG, JPEG, TXT",
        )

    report_id = f"rep_{uuid.uuid4().hex[:12]}"

    try:
        if suffix == ".pdf":
            file.file.seek(0, 2)
            size_bytes = file.file.tell()
            file.file.seek(0)

            classify_result = load_and_classify(_FileLikeWrapper(file), file.filename, size_bytes)
            file_path = str(classify_result["file_path"])
            pdf_type = classify_result["pdf_type"]  # "text" or "scanned"
        else:
            file.file.seek(0, 2)
            size_bytes = file.file.tell()
            file.file.seek(0)

            if size_bytes > config.MAX_UPLOAD_SIZE_BYTES:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File exceeds the 25MB size limit.")
            if size_bytes == 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

            saved_path = _save_generic_file(file)
            file_path = str(saved_path)
            pdf_type = "image" if suffix in [".png", ".jpg", ".jpeg"] else "text_file"

        # Create an initial (unprocessed) report entry so /process, /history,
        # etc. all have something to look up by report_id from this point on.
        save_report({
            "report_id": report_id,
            "file_path": file_path,
            "pdf_type": pdf_type,
            "patient": {},
            "laboratory_results": [],
            "doctor_notes": {},
            "ai_summary": {},
            "generated_summary": {},
            "diet_recommendations": {},
            "translation": {},
            "pdf_path": None,
            "status": "uploaded",
        })

        logger.info("Uploaded report %s (%s) -> %s", report_id, pdf_type, file_path)

        return UploadResponse(
            report_id=report_id,
            file_name=file.filename,
            file_path=file_path,
            pdf_type=pdf_type,
            success=True,
            message="File uploaded and classified successfully.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Upload failed: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {str(e)}")
