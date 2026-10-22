"""
Notice Classification Engine
Classifies recruitment notices into distinct, accurate record types:
- New recruitment notification
- Open application
- Closed recruitment
- Recruitment addendum or corrigendum
- Examination notification
- Admit card or call letter
- Result announcement
- General recruitment clarification

Ensures active-vacancy badges are ONLY shown when the application window is verified open.
"""

import re
from datetime import datetime, date


def parse_date_string(date_str):
    """
    Attempts to parse date string into a date object.
    Supports formats like 'YYYY-MM-DD', 'DD Month YYYY', etc.
    """
    if not date_str:
        return None
    s = str(date_str).strip()
    
    # Try YYYY-MM-DD
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        pass

    # Try common formats like "16 August 2025", "16-08-2025", "16/08/2025"
    for fmt in ["%d %B %Y", "%d %b %Y", "%d-%m-%Y", "%d/%m/%Y"]:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass

    return None


def classify_notice(record):
    """
    Deterministically classifies a notice record based on title, content, dates, and source metadata.
    Returns: dict with updated record_type, status, status_label, badge_type, and is_open_vacancy.
    """
    if record.get("is_historical"):
        return {
            "record_type": "historical_archive",
            "status": "Archived",
            "status_label": "Archived Notice (2025)",
            "badge_type": "archived",
            "is_open_vacancy": False
        }

    title = record.get("title", "")
    low = title.lower()

    # 1. Result announcement
    result_keywords = [
        "written result", "final result", "result:", "marks of recommended",
        "reserve list", "selection list", "merit list", "cutoff marks", "cut-off marks"
    ]
    if any(k in low for k in result_keywords):
        return {
            "record_type": "result_announcement",
            "status": "Result Declared",
            "status_label": "Result Announcement",
            "badge_type": "result",
            "is_open_vacancy": False
        }

    # 2. Admit Card / Call Letter
    admit_keywords = [
        "call letter", "admit card", "hall ticket", "e-admit card",
        "online exam call letter", "interview call letter"
    ]
    if any(k in low for k in admit_keywords):
        return {
            "record_type": "admit_card_call_letter",
            "status": "Call Letter Available",
            "status_label": "Admit Card / Call Letter",
            "badge_type": "call_letter",
            "is_open_vacancy": False
        }

    # 3. Recruitment Addendum or Corrigendum
    addendum_keywords = [
        "addendum", "corrigendum", "change in recruitment", "cancellation",
        "notice regarding change", "extension of last date", "extended last date",
        "amendment", "postponement", "kept on hold"
    ]
    if any(k in low for k in addendum_keywords):
        return {
            "record_type": "addendum_corrigendum",
            "status": "Notice Update",
            "status_label": "Addendum / Corrigendum",
            "badge_type": "addendum",
            "is_open_vacancy": False
        }

    # 4. Examination Notification / Schedule
    exam_keywords = [
        "examination time table", "interview schedule", "time table:",
        "rectt. test", "recruitment test:", "scheme of examination",
        "date of examination", "schedule of examination", "annual calendar"
    ]
    if any(k in low for k in exam_keywords):
        return {
            "record_type": "exam_notification",
            "status": "Exam Scheduled",
            "status_label": "Examination Schedule",
            "badge_type": "exam_schedule",
            "is_open_vacancy": False
        }

    # 5. General Recruitment Clarification / Advisory
    clarification_keywords = [
        "clarification", "advisory", "notice regarding", "representation",
        "time-frame representation", "instructions to candidates", "general notice"
    ]
    if any(k in low for k in clarification_keywords):
        return {
            "record_type": "general_clarification",
            "status": "Official Notice",
            "status_label": "Official Clarification",
            "badge_type": "clarification",
            "is_open_vacancy": False
        }

    # 6. Recruitment Notification / Open Vacancy
    # Check deadline status
    last_date_str = record.get("last_date", "")
    deadline_date = parse_date_string(last_date_str)
    today = date.today()

    if deadline_date:
        if deadline_date < today:
            # Deadline has passed
            return {
                "record_type": "closed_recruitment",
                "status": "Closed",
                "status_label": "Application Closed",
                "badge_type": "closed",
                "is_open_vacancy": False
            }
        else:
            # Deadline is known and active in future
            return {
                "record_type": "open_application",
                "status": "Open",
                "status_label": "Active Vacancy (Open)",
                "badge_type": "active_vacancy",
                "is_open_vacancy": True
            }

    # Deadline is unknown or "Refer Official Circular"
    # An unknown deadline must NOT automatically mean an active vacancy!
    return {
        "record_type": "new_recruitment",
        "status": "Notice Published",
        "status_label": "Official Notification",
        "badge_type": "official_notice",
        "is_open_vacancy": False
    }
