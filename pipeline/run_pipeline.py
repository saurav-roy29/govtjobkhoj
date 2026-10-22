"""
Pipeline Runner CLI
Orchestrates collection, normalization, validation, deduplication, and publishing.
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.config import (
    OFFICIAL_SOURCES,
    STAGING_JOBS_PATH,
    JOBS_JSON_PATH
)
from pipeline.collectors.upsc import UPSCCollector
from pipeline.collectors.ibps import IBPSCollector
from pipeline.collectors.feed import FeedCollector
from pipeline.normalizer import normalize_record
from pipeline.merger import merge_and_publish

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("PipelineRunner")

COLLECTOR_REGISTRY = {
    "UPSCCollector": UPSCCollector,
    "IBPSCollector": IBPSCollector,
    "FeedCollector": FeedCollector
}


def run_pipeline():
    logger.info("=== Starting GovtJobKhoj Recruitment Data Pipeline ===")
    all_raw_collected = []
    source_stats = {}

    for source in OFFICIAL_SOURCES:
        if not source.get("enabled"):
            logger.info(f"Skipping disabled source: {source['name']}")
            continue

        collector_class_name = source.get("collector_class")
        collector_cls = COLLECTOR_REGISTRY.get(collector_class_name)
        if not collector_cls:
            logger.warning(f"No collector class found for {collector_class_name}")
            continue

        logger.info(f"Running collector: {source['name']} ({source['url']})")
        collector = collector_cls(source)
        try:
            notices = collector.collect()
            source_stats[source["id"]] = {
                "name": source["name"],
                "collected": len(notices),
                "url": source["url"]
            }
            all_raw_collected.extend(notices)
        except Exception as e:
            logger.error(f"Error during collection from {source['name']}: {e}", exc_info=True)
            source_stats[source["id"]] = {
                "name": source["name"],
                "collected": 0,
                "error": str(e)
            }

    logger.info(f"Total raw notices extracted across sources: {len(all_raw_collected)}")

    # Normalize records
    normalized_records = []
    # Temporary ID placeholder; merger assigns final sequential IDs
    for idx, raw in enumerate(all_raw_collected, start=1001):
        norm = normalize_record(raw, assigned_id=idx)
        normalized_records.append(norm)

    # Save to staging_jobs.json for transparency and inspection
    with open(STAGING_JOBS_PATH, "w", encoding="utf-8") as f:
        json.dump(normalized_records, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(normalized_records)} normalized records to {STAGING_JOBS_PATH}")

    # Merge and publish approved notices
    result = merge_and_publish(normalized_records)

    logger.info("=== Pipeline Execution Complete ===")
    print("\n" + "=" * 60)
    print("PIPELINE EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Timestamp:             {datetime.now().isoformat()}")
    print(f"Sources Tested:        {len(source_stats)}")
    for sid, info in source_stats.items():
        err = f" (Error: {info['error']})" if "error" in info else ""
        print(f" - {info['name']}: {info['collected']} notices{err}")
    print(f"Preserved Historical: {result['historical_preserved']} listings")
    print(f"New Approved Notices:  {result['new_approved']} listings")
    print(f"Existing Updated:      {result['existing_updated']} notices")
    print(f"Flagged for Review:    {result['pending_review']} notices (quarantined)")
    print(f"Final Total Published: {result['total_final']} notices in jobs.json")
    print("=" * 60)

    return result


if __name__ == "__main__":
    run_pipeline()
