"""
response_models.py
--------------------
Pydantic models for outgoing responses. Field names match the
project-wide variable naming convention exactly:

    report_id, patient, laboratory_results, doctor_notes, ai_summary,
    generated_summary, diet_recommendations, translation, pdf_path
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class UploadResponse(BaseModel):
    report_id: str
    file_name: str
    file_path: str
    pdf_type: str
    success: bool
    message: str


class ProcessResponse(BaseModel):
    report_id: str
    patient: Dict[str, Any]
    laboratory_results: List[Dict[str, Any]]
    doctor_notes: Dict[str, Any]
    ai_summary: Dict[str, Any]
    generated_summary: Dict[str, Any]
    diet_recommendations: Dict[str, Any]
    success: bool
    message: str


class SummaryResponse(BaseModel):
    report_id: str
    patient: Dict[str, Any]
    laboratory_results: List[Dict[str, Any]]
    doctor_notes: Dict[str, Any]
    ai_summary: Dict[str, Any]
    generated_summary: Dict[str, Any]
    diet_recommendations: Dict[str, Any]
    translation: Dict[str, Any]
    pdf_path: Optional[str] = None
    created_at: str


class DeleteResponse(BaseModel):
    report_id: str
    deleted: bool
    message: str


class TranslateResponse(BaseModel):
    report_id: str
    language: str
    translation: Dict[str, Any]
    success: bool


class GeneratePDFResponse(BaseModel):
    report_id: str
    pdf_path: str
    success: bool


class HistoryItem(BaseModel):
    report_id: str
    patient_name: Optional[str] = None
    created_at: str
    status: str


class HistoryResponse(BaseModel):
    reports: List[HistoryItem]
    total: int
