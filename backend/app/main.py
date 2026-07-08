"""
main.py
--------
FastAPI application entry point. Wires together all route modules.
Run with:
    uvicorn backend.app.main:app --reload
"""

import logging
import sys
from datetime import datetime, timezone

# config MUST be imported first -- it sets up sys.path for every
# sibling package (ai_summary, translation, pdf_generator, etc.)
import backend.app.config  # noqa: F401

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.routes import upload, process, summary, translate, download, history

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("medical_report_backend")

app = FastAPI(
    title="AI Medical Report Summarizer API",
    description="Backend service for uploading, processing (OCR + extraction + AI summary), translating, and downloading medical report summaries.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: str


@app.get("/health", response_model=HealthResponse)
def get_health():
    """Simple health check."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


# ---------------------------------------------------------------
# Routers -- route paths are defined inside each router module and
# match the frontend's expected endpoints exactly:
#   POST /upload, POST /process, GET+DELETE /summary/{report_id},
#   POST /translate, POST /generate-pdf, GET /history
# ---------------------------------------------------------------
app.include_router(upload.router, tags=["Upload"])
app.include_router(process.router, tags=["Process"])
app.include_router(summary.router, tags=["Summary"])
app.include_router(translate.router, tags=["Translate"])
app.include_router(download.router, tags=["Download"])
app.include_router(history.router, tags=["History"])

logger.info("AI Medical Report Summarizer backend initialized.")
