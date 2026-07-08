# 🏥 HealthPulse AI - Medical Report Summarizer

HealthPulse AI is a complete, production-ready full-stack medical analysis platform. It integrates a multi-stage pipeline—including document parsing, scanned-PDF OCR, regex-based medical entity extraction, dual LLM summarization (Gemini & OpenAI with local fallback), multi-lingual translation, and auto-generated clinical PDF compilation—into an interactive clinical dashboard.

---

## 🏗️ Architecture & Processing Pipeline

```
          [ Streamlit Frontend Desk ]
                       │ (real HTTP calls)
                       ▼
            [ FastAPI Backend App ]
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
[ Text-based Documents ]     [ Scanned Documents / Images ]
  - PyPDF2 Parser              - pdf2image converter
  - Text loader                - OpenCV image enhancer
                               - EasyOCR & Tesseract engines
         │                           │
         └─────────────┬─────────────┘
                       ▼
            [ regex_filters & clean_text ] (Normalizes OCR artifacts)
                       │
                       ▼
            [ Medical Info Extraction ] (Regex extract Name, Lab Parameters, Attending Doctor, Hospital)
                       │
                       ▼
            [ Dual LLM Summarization ] (Prompts LLM for diagnostic highlights, diet, and lifestyle recommendations)
                       │
                       ▼
         ┌─────────────┴─────────────┐
         ▼                           ▼
[ Translation Module ]       [ ReportLab PDF Generator ] (Draws high-fidelity A4 layout)
  - Hindi, Telugu, Tamil       - Saves summary report to disk
         │                           │
         └─────────────┬─────────────┘
                       ▼
          [ Persistent SQLite Vault ] (History log database)
```

---

## 📦 Prerequisites & System Setup

### 1. External Dependencies (Optional)
*   **Poppler**: Required for converting PDF pages to images. On Windows:
    1.  Download from [github.com/oschwartz10612/poppler-windows/releases](https://github.com/oschwartz10612/poppler-windows/releases).
    2.  Extract it and add the `bin/` directory path to your system's environment `PATH` variable.
*   **Tesseract OCR**: Required for OCR fallback. On Windows:
    1.  Download installer from [github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki).
    2.  Add its installation folder (default `C:\Program Files\Tesseract-OCR`) to your system's `PATH`.

### 2. Python Environment Setup
Install the consolidated requirements:
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root workspace directory:
```env
# API Keys (Provide one or both to enable real LLM generation; otherwise, the app auto-degrades to rule-based fallback summaries)
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# OCR & Engine Configs (Defaults are fine)
UPLOAD_DIR=./uploads
IMAGE_DPI=300
```

---

## 🚀 Execution Guide

To run the application, start the backend API server and frontend dashboard concurrently:

### 1. Spin Up FastAPI Backend
Run the backend web server from the workspace directory:
```bash
python backend/app/main.py
```
*   The interactive Swagger documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
*   The server binds to port `8000`.

### 2. Spin Up Streamlit Frontend
In a separate terminal window, launch the Streamlit app:
```bash
streamlit run frontend/app.py
```
*   The dashboard portal will open automatically at [http://localhost:8501](http://localhost:8501).

---

## 🔍 Verification & Features Checklist

1.  **Report Submission Desk**:
    *   Upload any `.pdf`, `.png`, `.jpg`, or `.txt` report.
    *   The app will classified it automatically (`text` PDF, `scanned` PDF, `image`, or `text_file`), perform OCR extraction, clean formatting anomalies, extract parameters, synthesize clinical findings, and compile the final PDF.
2.  **Diagnostic Synthesis Summary**:
    *   View structured patient information, laboratory biomarker analyte profiles with colored safety badges (`High`, `Low`, `Normal`), diagnostic clinician notes, and simplified AI recommendations.
3.  **Translation Portal**:
    *   Select your language of choice (Hindi, Telugu, Tamil, English) and click **Translate Summary**. The summary text and analytical bullets will translate immediately and update on screen.
4.  **Clinical Report Generation**:
    *   Click **Download PDF** to retrieve a highly polished, printable A4-compiled layout including lab profiles and lifestyle adjustments.
5.  **History Logs**:
    *   Browse previously processed reports in the historical records vault. Re-inspect summaries, download the generated PDFs, or purge older files.
