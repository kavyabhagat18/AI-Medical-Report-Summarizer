"""
db_service.py
--------------
Single responsibility: persist and retrieve report data. No pipeline
logic, no AI calls, no PDF/translation work -- just CRUD against the
reports table.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.database.database import get_connection, init_db

logger = logging.getLogger(__name__)

# Make sure the table exists as soon as this module is imported.
init_db()


def save_report(report: Dict[str, Any]) -> None:
    """
    Insert a new report or overwrite an existing one (matched by report_id).

    Args:
        report: full report dict. Must contain "report_id".
    """
    report_id = report.get("report_id")
    if not report_id:
        raise ValueError("save_report() requires a 'report_id' key in the report dict.")

    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT created_at FROM reports WHERE report_id = ?", (report_id,)
        ).fetchone()
        created_at = existing["created_at"] if existing else now

        conn.execute(
            """
            INSERT INTO reports (report_id, data, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(report_id) DO UPDATE SET
                data = excluded.data,
                updated_at = excluded.updated_at
            """,
            (report_id, json.dumps(report), created_at, now),
        )
        conn.commit()
    finally:
        conn.close()


def get_report(report_id: str) -> Optional[Dict[str, Any]]:
    """Return the full report dict for a given report_id, or None if not found."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT data, created_at FROM reports WHERE report_id = ?", (report_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    report = json.loads(row["data"])
    report.setdefault("created_at", row["created_at"])
    return report


def get_all_reports() -> List[Dict[str, Any]]:
    """Return a lightweight summary list of every stored report, most recent first."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT report_id, data, created_at FROM reports ORDER BY created_at DESC"
        ).fetchall()
    finally:
        conn.close()

    summaries = []
    for row in rows:
        data = json.loads(row["data"])
        patient = data.get("patient") or {}
        summaries.append({
            "report_id": row["report_id"],
            "patient_name": patient.get("name"),
            "created_at": row["created_at"],
            "status": data.get("status", "unknown"),
        })
    return summaries


def delete_report(report_id: str) -> bool:
    """Delete a report by ID. Returns True if a row was deleted, False if it didn't exist."""
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM reports WHERE report_id = ?", (report_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
