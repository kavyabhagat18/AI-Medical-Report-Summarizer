"""
request_models.py
-------------------
Pydantic models for incoming request bodies. Field names match the
project-wide variable naming convention exactly (report_id, etc.) so
the frontend's request payloads line up with zero translation.
"""

from pydantic import BaseModel, Field


class ProcessRequest(BaseModel):
    """Body for POST /process -- kicks off OCR -> extraction -> AI summary for an uploaded report."""
    report_id: str = Field(..., description="ID returned by POST /upload")


class TranslateRequest(BaseModel):
    """Body for POST /translate -- translates an already-generated summary."""
    report_id: str = Field(..., description="ID of a report that has already been processed")
    language: str = Field(..., description="Target language, e.g. 'hindi', 'telugu', 'tamil', 'english'")


class GeneratePDFRequest(BaseModel):
    """Body for POST /generate-pdf -- builds a downloadable PDF for a processed report."""
    report_id: str = Field(..., description="ID of a report that has already been processed")
