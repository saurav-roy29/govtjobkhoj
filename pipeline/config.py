"""
GovtJobKhoj Pipeline Configuration
Configures official recruitment sources, request policies, and validation rules.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
JS_DIR = BASE_DIR / "js"

JOBS_JSON_PATH = DATA_DIR / "jobs.json"
HISTORICAL_JOBS_PATH = DATA_DIR / "historical_jobs.json"
STAGING_JOBS_PATH = DATA_DIR / "staging_jobs.json"
PENDING_REVIEW_PATH = DATA_DIR / "pending_review.json"
DATA_JS_PATH = JS_DIR / "data.js"

# Polite Request Configuration
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 (GovtJobKhoj-PublicMonitor/1.0)"
REQUEST_TIMEOUT_SECONDS = 15
REQUEST_INTERVAL_SECONDS = 1.0  # Polite crawl delay between calls to same host
MAX_RETRIES = 2

# Official Sources Configuration
OFFICIAL_SOURCES = [
    {
        "id": "upsc_whats_new",
        "name": "Union Public Service Commission (UPSC)",
        "type": "html_scraper",
        "collector_class": "UPSCCollector",
        "sector": "Central Government",
        "category": "Central Govt",
        "url": "https://www.upsc.gov.in/whats-new",
        "domain": "upsc.gov.in",
        "enabled": True,
        "description": "Authoritative central civil services, defence, and engineering recruitment notices."
    },
    {
        "id": "ibps_active",
        "name": "Institute of Banking Personnel Selection (IBPS)",
        "type": "html_scraper",
        "collector_class": "IBPSCollector",
        "sector": "Banking",
        "category": "Banks Job",
        "url": "https://www.ibps.in",
        "domain": "ibps.in",
        "enabled": True,
        "description": "Authoritative public sector bank recruitment circulars (Clerk, PO, RRB, SO)."
    },
    {
        "id": "official_rss_feed",
        "name": "Configurable Official RSS/Atom Feed",
        "type": "feed",
        "collector_class": "FeedCollector",
        "sector": "Central Government",
        "category": "Central Govt",
        "url": "",  # Optional configurable feed URL
        "domain": "",
        "enabled": False,
        "description": "Generic adapter for official government portals with published RSS/XML feeds."
    }
]

# Known Authoritative Domains for Link Verification
AUTHORITATIVE_DOMAINS = [
    "upsc.gov.in",
    "upsconline.nic.in",
    "ibps.in",
    "ibpsreg.ibps.in",
    "sbi.co.in",
    "rbi.org.in",
    "pnbindia.in",
    "bankofbaroda.in",
    "centralbankofindia.co.in",
    "punjabandsindbank.co.in",
    "brbnmpl.co.in",
    "unionbankofindia.co.in",
    "iob.in",
    "ucobank.com",
    "mscbank.com",
    "bankofmaharashtra.in",
    "tmbnet.in",
    "nabard.org",
    "bobcaps.in",
    "ncs.gov.in",
    "ssc.gov.in",
    "drdo.gov.in",
    "isro.gov.in",
    "bihar.gov.in",
    "gov.in",
    "nic.in"
]
