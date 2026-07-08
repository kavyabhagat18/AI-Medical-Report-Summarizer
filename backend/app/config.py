"""
config.py
----------
Central configuration for the backend.

Responsibilities:
    - Wire up sys.path so sibling top-level packages (pdf_processing, ocr,
      text_processing, medical_information_extraction, ai_summary,
      translation, pdf_generator) can be imported cleanly from anywhere
      in backend/app/.
    - Hold shared settings: file paths, size limits, allowed extensions.

IMPORTANT: this module must be imported BEFORE any sibling-package
imports elsewhere in the backend, since it's what sets up sys.path.
main.py imports this first, and every route/service module that needs
a sibling package imports `backend.app.config` (even just for the
side effect) before importing e.g. `ai_summary.prompt`.
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------
# Prevent google-genai's Client from crashing at import time if no
# real Gemini key is set yet (e.g. during local dev / testing).
# ---------------------------------------------------------------
if not os.environ.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = "DUMMY_KEY_TO_PREVENT_STARTUP_CRASH"

# ---------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------
# backend/app/config.py -> parents[2] = project root
ROOT_DIR = Path(__file__).resolve().parents[2]

# Make sibling top-level packages importable
for sub_path in [
    ROOT_DIR,
    ROOT_DIR / "text_processing",
    ROOT_DIR / "ai_summary",
    ROOT_DIR / "translation" / "Translation_Module",
    ROOT_DIR / "pdf_generator",
]:
    sub_path_str = str(sub_path)
    if sub_path_str not in sys.path:
        sys.path.append(sub_path_str)

# ---------------------------------------------------------------
# Shared settings
# ---------------------------------------------------------------
UPLOAD_DIR = ROOT_DIR / "uploads"
OUTPUT_DIR = ROOT_DIR / "outputs"
DB_PATH = Path(__file__).resolve().parent / "database" / "history.db"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

ALLOWED_UPLOAD_SUFFIXES = [".pdf", ".png", ".jpg", ".jpeg", ".txt"]
MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024  # 25MB

SUPPORTED_LANGUAGES = ["english", "hindi", "telugu", "tamil"]
