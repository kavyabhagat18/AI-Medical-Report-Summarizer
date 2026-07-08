"""
database.py
------------
SQLite setup for report history.

Stores each report as ONE row: report_id (primary key) + the full report
JSON blob (patient, laboratory_results, doctor_notes, ai_summary,
generated_summary, diet_recommendations, translation, pdf_path, etc.)
serialized as text. Keeping the whole report as one JSON blob (rather
than a rigid multi-column schema) means the medical extraction / AI
summary teams can evolve their JSON shape without needing a database
migration every time -- db_service.py is the only place that needs to
know how to read/write it.
"""

import sqlite3
from pathlib import Path

from backend.app.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Open a new SQLite connection to the history database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the reports table if it doesn't already exist. Safe to call on every startup."""
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                report_id   TEXT PRIMARY KEY,
                data        TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
