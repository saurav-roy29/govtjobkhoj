"""
Validator
Validates candidate recruitment records against schema constraints, official domain
requirements, and flags uncertain or incomplete records for manual review.
"""

from urllib.parse import urlparse
from pipeline.config import AUTHORITATIVE_DOMAINS


def is_authoritative_url(url):
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        hostname = hostname.lower()
        return any(hostname == d or hostname.endswith("." + d) for d in AUTHORITATIVE_DOMAINS)
    except Exception:
        return False


def validate_notice(record):
    """
    Validates a normalized notice record.
    Returns: (is_approved: bool, is_uncertain: bool, reason: str)
    """
    title = record.get("title", "").strip()
    if not title or len(title) < 12:
        return False, True, "Title is missing or too short (< 12 chars)"

    org = record.get("org", "").strip()
    if not org:
        return False, True, "Organization name is missing"

    official_links = record.get("official_links", [])
    if not official_links:
        return False, True, "No official notification or portal links provided"

    has_authoritative = any(is_authoritative_url(l.get("url", "")) for l in official_links)
    if not has_authoritative:
        return False, True, "None of the provided links resolve to recognized official government/commission domains"

    content_html = record.get("content_html", "").strip()
    if not content_html or len(content_html) < 40:
        return False, True, "Notice content HTML is missing or too short"

    return True, False, "Approved - Passed all official schema and domain checks"
