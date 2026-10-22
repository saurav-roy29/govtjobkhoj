"""
Distribution Packaging Script for Hostinger Deployment
Stages ONLY production website files into _site/ directory for secure deployment.
Guarantees that pipeline scripts, internal review datasets, and repository metadata
are strictly excluded from the public_html web root.
"""

import json
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "_site"

def prepare_dist():
    print("======================================================================")
    print("       PREPARING PRODUCTION DISTRIBUTION FOR HOSTINGER DEPLOYMENT")
    print("======================================================================\n")

    # Clean existing _site directory if present
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copy HTML pages
    html_files = list(BASE_DIR.glob("*.html"))
    for hf in html_files:
        shutil.copy2(hf, DIST_DIR / hf.name)
    print(f"Staged {len(html_files)} HTML pages.")

    # 2. Copy favicon and root assets
    root_assets = ["favicon.ico", ".htaccess"]
    for asset in root_assets:
        asset_path = BASE_DIR / asset
        if asset_path.exists():
            shutil.copy2(asset_path, DIST_DIR / asset)
            print(f"Staged root asset: {asset}")

    # 3. Copy css/ directory
    css_src = BASE_DIR / "css"
    if css_src.exists():
        shutil.copytree(css_src, DIST_DIR / "css")
        print("Staged css/ directory.")

    # 4. Copy js/ directory
    js_src = BASE_DIR / "js"
    if js_src.exists():
        shutil.copytree(js_src, DIST_DIR / "js")
        print("Staged js/ directory.")

    # 5. Copy assets/ directory (images, icons)
    assets_src = BASE_DIR / "assets"
    if assets_src.exists():
        shutil.copytree(assets_src, DIST_DIR / "assets")
        print("Staged assets/ directory.")

    # 6. Copy ONLY data/jobs.json (exclude staging_jobs.json, pending_review.json, historical_jobs.json)
    data_dist = DIST_DIR / "data"
    data_dist.mkdir(parents=True, exist_ok=True)
    jobs_json_src = BASE_DIR / "data" / "jobs.json"
    if jobs_json_src.exists():
        shutil.copy2(jobs_json_src, data_dist / "jobs.json")
        print("Staged data/jobs.json (ONLY production dataset).")
    else:
        print("ERROR: data/jobs.json missing!", file=sys.stderr)
        sys.exit(1)

    # 7. Verification of staged distribution
    print("\n--- [VERIFYING STAGED DISTRIBUTION] ---")
    staged_jobs_path = data_dist / "jobs.json"
    with open(staged_jobs_path, "r", encoding="utf-8") as f:
        staged_jobs = json.load(f)
    print(f"Verified staged jobs.json record count: {len(staged_jobs)}")

    # Verify no prohibited files leaked into _site
    prohibited_patterns = [
        "*.py", "staging_jobs.json", "pending_review.json",
        "historical_jobs.json", "requirements.txt", ".git*"
    ]
    leaks = []
    for pattern in prohibited_patterns:
        leaks.extend(list(DIST_DIR.rglob(pattern)))

    if leaks:
        print(f"ERROR: Prohibited files leaked into distribution: {leaks}", file=sys.stderr)
        sys.exit(1)

    # Calculate total staged file count and size
    all_staged = list(DIST_DIR.rglob("*"))
    files_only = [f for f in all_staged if f.is_file()]
    total_size_bytes = sum(f.stat().st_size for f in files_only)
    total_size_mb = total_size_bytes / (1024 * 1024)

    print(f"Total production files staged: {len(files_only)}")
    print(f"Total distribution payload size: {total_size_mb:.2f} MB")
    print("\nDistribution artifact successfully built at _site/")
    print("======================================================================\n")

if __name__ == "__main__":
    prepare_dist()
