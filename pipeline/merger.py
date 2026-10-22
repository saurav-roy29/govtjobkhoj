"""
Merger
Safely merges newly validated recruitment notices with the preserved historical dataset,
detects duplicates and changes, and updates both data/jobs.json and js/data.js.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import re
from pipeline.config import (
    JOBS_JSON_PATH,
    HISTORICAL_JOBS_PATH,
    PENDING_REVIEW_PATH,
    DATA_JS_PATH,
    STAGING_JOBS_PATH
)
from pipeline.validator import validate_notice

logger = logging.getLogger(__name__)


def title_fingerprint(title):
    clean = re.sub(r'[^a-z0-9]', '', title.lower())
    return clean[:60]


def load_historical_baseline():
    """
    Loads or initializes the immutable historical 20 listings archive.
    """
    if HISTORICAL_JOBS_PATH.exists():
        with open(HISTORICAL_JOBS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    # If historical_jobs.json does not exist yet, create it from existing jobs.json
    if JOBS_JSON_PATH.exists():
        with open(JOBS_JSON_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)
        # Ensure is_historical flag is set on the baseline
        for item in existing:
            item["is_historical"] = True
            item["status"] = "Archived"
            item["status_label"] = "Archived Notice (2025)"
        with open(HISTORICAL_JOBS_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        logger.info(f"Created immutable historical baseline with {len(existing)} records at {HISTORICAL_JOBS_PATH}")
        return existing

    return []


def merge_and_publish(new_records):
    """
    Merges validated new records into the production dataset.
    """
    historical_records = load_historical_baseline()
    logger.info(f"Loaded {len(historical_records)} preserved historical records.")

    # Load existing production dataset if present
    existing_records = []
    if JOBS_JSON_PATH.exists():
        with open(JOBS_JSON_PATH, "r", encoding="utf-8") as f:
            existing_records = json.load(f)

    # Build lookup indices for duplicate and change detection
    existing_by_url = {}
    existing_by_fp = {}
    used_ids = set()

    for item in existing_records:
        used_ids.add(item.get("id"))
        s_url = item.get("source_url")
        if s_url:
            existing_by_url[s_url] = item
        fp = title_fingerprint(item.get("title", ""))
        if fp:
            existing_by_fp[fp] = item

    for item in historical_records:
        used_ids.add(item.get("id"))

    next_id = max(used_ids, default=200) + 1

    approved_new = []
    pending_review = []
    updated_count = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    # Process incoming records
    for raw in new_records:
        # Validate record
        is_approved, is_uncertain, reason = validate_notice(raw)
        if not is_approved:
            pending_review.append({
                "record": raw,
                "reason": reason,
                "flagged_at": now_iso
            })
            continue

        raw_url = raw.get("source_url")
        raw_fp = title_fingerprint(raw.get("title", ""))

        # Check for duplicate / change detection
        match = existing_by_url.get(raw_url) or existing_by_fp.get(raw_fp)
        if match:
            # Change detection: update verification date, classification, and deadlines
            match["last_verified_at"] = now_iso
            for field in ["record_type", "badge_type", "status", "status_label", "is_open_vacancy", "categories", "official_links"]:
                if field in raw:
                    match[field] = raw[field]
            if raw.get("last_date") and raw.get("last_date") != match.get("last_date"):
                match["last_date"] = raw["last_date"]
                logger.info(f"Updated deadline for notice {match['id']}: {raw['last_date']}")
            updated_count += 1
            continue

        # New unique approved notice
        raw["id"] = next_id
        raw["is_historical"] = False
        raw["retrieved_at"] = now_iso
        raw["last_verified_at"] = now_iso
        approved_new.append(raw)
        used_ids.add(next_id)
        next_id += 1

    # Ensure historical baseline records have complete classification metadata
    for h in historical_records:
        h["is_historical"] = True
        h["status"] = "Archived"
        h["status_label"] = "Archived Notice (2025)"
        h["badge_type"] = "archived"
        h["record_type"] = "historical_listing"

    # Preserve all historical listings + existing live notices + approved new notices
    # Use a dictionary by ID to ensure strict uniqueness
    final_dataset_map = {}
    historical_ids = {h["id"] for h in historical_records}

    # First add live existing records (excluding any historical IDs)
    for ex in existing_records:
        if ex.get("id") not in historical_ids:
            final_dataset_map[ex["id"]] = ex

    # Add the historical baseline records
    for h in historical_records:
        final_dataset_map[h["id"]] = h

    # Add new approved notices
    for ann in approved_new:
        final_dataset_map[ann["id"]] = ann

    final_dataset = list(final_dataset_map.values())
    # Sort with active/latest notices first, preserving order
    final_dataset.sort(key=lambda x: (not x.get("is_historical", False), x.get("publish_date", "")), reverse=True)

    # Save data/jobs.json
    with open(JOBS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(final_dataset, f, indent=2, ensure_ascii=False)
    logger.info(f"Published {len(final_dataset)} total notices to {JOBS_JSON_PATH}")

    # Synchronize js/data.js (bundled window.GJK_JOBS_DATA)
    js_content = "/**\n" \
                 " * GovtJobKhoj Verified Jobs Dataset\n" \
                 " * Contains preserved historical notices and verified active recruitment notices\n" \
                 " */\n" \
                 f"window.GJK_JOBS_DATA = {json.dumps(final_dataset, indent=2, ensure_ascii=False)};\n"
    with open(DATA_JS_PATH, "w", encoding="utf-8") as f:
        f.write(js_content)
    logger.info(f"Synchronized window.GJK_JOBS_DATA in {DATA_JS_PATH}")

    # Save pending review queue
    with open(PENDING_REVIEW_PATH, "w", encoding="utf-8") as f:
        json.dump(pending_review, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(pending_review)} flagged records to {PENDING_REVIEW_PATH}")

    return {
        "total_final": len(final_dataset),
        "historical_preserved": len(historical_records),
        "new_approved": len(approved_new),
        "existing_updated": updated_count,
        "pending_review": len(pending_review)
    }
