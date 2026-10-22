"""
Normalizer
Normalizes raw collector records to match the frontend schema expectations and
applies the rigorous notice classification engine.
"""

import re
from datetime import datetime, timezone
from pipeline.classifier import classify_notice


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'[^a-z0-9\-]', '', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:100]


def normalize_record(raw_record, assigned_id):
    """
    Normalizes a single collector record to strictly conform to frontend schema.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    title = raw_record.get("title", "").strip()
    slug = slugify(f"{assigned_id}-{title}")

    # Official links cleanup
    cleaned_links = []
    for link in raw_record.get("official_links", []):
        url = link.get("url", "").strip()
        text = link.get("text", "Official Link").strip()
        if url.startswith("http://") or url.startswith("https://"):
            cleaned_links.append({"url": url, "text": text})

    # Apply deterministic classification
    classification = classify_notice(raw_record)

    return {
        "id": assigned_id,
        "title": title,
        "slug": slug,
        "org": raw_record.get("org", "Government of India").strip(),
        "sector": raw_record.get("sector", "Central Government"),
        "vacancies": str(raw_record.get("vacancies", "Refer Circular")),
        "last_date": raw_record.get("last_date", "Refer Circular"),
        "publish_date": raw_record.get("publish_date", datetime.now().strftime("%Y-%m-%d")),
        "app_mode": raw_record.get("app_mode", "Online"),
        "status": classification["status"],
        "status_label": classification["status_label"],
        "record_type": classification["record_type"],
        "badge_type": classification["badge_type"],
        "is_open_vacancy": classification["is_open_vacancy"],
        "qualification": raw_record.get("qualification", "Refer Official Notification"),
        "categories": raw_record.get("categories", ["Central Govt"]),
        "official_links": cleaned_links,
        "content_html": raw_record.get("content_html", f"<p>{title}</p>"),
        # Pipeline audit metadata
        "source_url": raw_record.get("source_url", ""),
        "retrieved_at": now_iso,
        "last_verified_at": now_iso,
        "verification_status": "verified_official",
        "is_historical": False
    }
