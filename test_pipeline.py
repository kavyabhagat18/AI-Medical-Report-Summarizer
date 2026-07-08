import httpx
import sys
import time

BACKEND_URL = "http://127.0.0.1:8000"

def run_test():
    print("Testing backend pipeline...")
    
    # 1. Check health
    try:
        r = httpx.get(f"{BACKEND_URL}/health", timeout=5.0)
        print(f"Health check status: {r.status_code}, Response: {r.json()}")
    except Exception as e:
        print(f"ERROR: Could not connect to backend at {BACKEND_URL}. Is it running? Details: {e}")
        sys.exit(1)
        
    # 2. Upload file
    print("Uploading sample_report.txt...")
    files = {"file": ("sample_report.txt", open("sample_report.txt", "rb"), "text/plain")}
    r = httpx.post(f"{BACKEND_URL}/upload", files=files, timeout=10.0)
    if r.status_code != 200:
        print(f"ERROR: Upload failed: {r.status_code} - {r.text}")
        sys.exit(1)
        
    upload_data = r.json()
    print("Upload success:", upload_data)
    report_id = upload_data["report_id"]
    file_path = upload_data["file_path"]
    pdf_type = upload_data["pdf_type"]
    
    # 3. Process report
    print(f"Processing report ID {report_id}...")
    payload = {
        "report_id": report_id,
        "file_path": file_path,
        "pdf_type": pdf_type
    }
    r = httpx.post(f"{BACKEND_URL}/process", json=payload, timeout=60.0)
    if r.status_code != 200:
        print(f"ERROR: Processing failed: {r.status_code} - {r.text}")
        sys.exit(1)
        
    print("Processing success!")
    
    # 4. Get summary (Retrieve to verify ResponseValidationError is gone)
    print(f"Retrieving summary for {report_id}...")
    r = httpx.get(f"{BACKEND_URL}/summary/{report_id}", timeout=10.0)
    if r.status_code != 200:
        print(f"ERROR: Summary retrieval failed: {r.status_code} - {r.text}")
        sys.exit(1)
        
    summary_data = r.json()
    print("SUCCESS: Summary retrieved correctly!")
    print(f"Patient Name: {summary_data.get('patient_name')}")
    print(f"Report Type: {summary_data.get('report_type')}")
    print(f"Lab Results Count: {len(summary_data.get('lab_results', []))}")
    print("All checks passed successfully!")

if __name__ == "__main__":
    run_test()
