import httpx
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

BACKEND_URL = "http://127.0.0.1:8000"

def upload_report(file_bytes: bytes, file_name: str, file_type: str) -> Dict[str, Any]:
    """
    Uploads a medical report and processes it immediately through the pipeline.
    
    Args:
        file_bytes: Content of the file in bytes.
        file_name: Name of the uploaded file.
        file_type: MIME type of the file.
        
    Returns:
        Dict: Contains success status, message, and report_id.
    """
    try:
        # Step 1: Upload the file
        logger.info("Uploading file %s to backend...", file_name)
        files = {"file": (file_name, file_bytes, file_type or "application/octet-stream")}
        
        with httpx.Client(timeout=60.0) as client:
            upload_response = client.post(f"{BACKEND_URL}/upload", files=files)
            if upload_response.status_code != 200:
                logger.error("Upload failed: %s", upload_response.text)
                return {
                    "success": False,
                    "message": f"Upload failed: {upload_response.json().get('detail', 'Unknown error')}"
                }
                
            upload_data = upload_response.json()
            report_id = upload_data["report_id"]
            file_path = upload_data["file_path"]
            pdf_type = upload_data["pdf_type"]
            
            logger.info("Upload success. ID: %s. Initiating document processing...", report_id)
            
            # Step 2: Process the report
            payload = {
                "report_id": report_id,
                "file_path": file_path,
                "pdf_type": pdf_type
            }
            
            process_response = client.post(f"{BACKEND_URL}/process", json=payload)
            if process_response.status_code != 200:
                logger.error("Processing failed: %s", process_response.text)
                return {
                    "success": False,
                    "message": f"Processing failed: {process_response.json().get('detail', 'Unknown error')}"
                }
                
            return {
                "report_id": report_id,
                "success": True,
                "message": "File processed and summarized successfully."
            }
            
    except Exception as e:
        logger.exception("Exception in upload_report client: %s", e)
        return {
            "success": False,
            "message": f"Connection error: {str(e)}"
        }

def get_summary(report_id: str) -> Dict[str, Any]:
    """
    Retrieves the parsed summary and lab parameters for a specific report.
    """
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{BACKEND_URL}/summary/{report_id}")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error("Failed to retrieve summary for %s: %s", report_id, response.text)
                raise Exception(response.json().get("detail", "Failed to retrieve summary"))
    except Exception as e:
        logger.exception("Error in get_summary client: %s", e)
        raise e

def translate_summary(report_id: str, target_language: str) -> Dict[str, Any]:
    """
    Translates the summary of the report to the target language.
    """
    try:
        payload = {
            "report_id": report_id,
            "language": target_language
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(f"{BACKEND_URL}/translate", json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error("Translation request failed: %s", response.text)
                return {
                    "success": False,
                    "language": target_language,
                    "translated_text": f"Error: {response.json().get('detail', 'Translation failed')}",
                    "translated_bullets": []
                }
    except Exception as e:
        logger.exception("Error in translate_summary client: %s", e)
        return {
            "success": False,
            "language": target_language,
            "translated_text": f"Connection error: {str(e)}",
            "translated_bullets": []
        }

def download_pdf(report_id: str) -> bytes:
    """
    Downloads the generated PDF report bytes from the backend.
    """
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(f"{BACKEND_URL}/generate-pdf", json={"report_id": report_id})
            if response.status_code == 200:
                return response.content
            else:
                logger.error("PDF generation/download request failed: %s", response.text)
                raise Exception(response.json().get("detail", "PDF generation failed"))
    except Exception as e:
        logger.exception("Error in download_pdf client: %s", e)
        raise e

def get_history() -> List[Dict[str, Any]]:
    """
    Retrieves the history of all processed reports.
    """
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{BACKEND_URL}/history")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error("Failed to retrieve report history: %s", response.text)
                return []
    except Exception as e:
        logger.exception("Error in get_history client: %s", e)
        return []

def delete_report(report_id: str) -> bool:
    """
    Deletes a report from history by its ID.
    """
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.delete(f"{BACKEND_URL}/summary/{report_id}")
            if response.status_code == 200:
                return response.json().get("success", False)
            else:
                logger.error("Failed to delete report: %s", response.text)
                return False
    except Exception as e:
        logger.exception("Error in delete_report client: %s", e)
        return False
