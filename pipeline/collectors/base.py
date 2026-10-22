"""
Base Collector Interface
Defines polite request handling, rate limiting, and robust error boundaries with curl fallback.
"""

import time
import logging
import subprocess
import requests
import urllib3
from pipeline.config import USER_AGENT, REQUEST_TIMEOUT_SECONDS, REQUEST_INTERVAL_SECONDS

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)


class FetchResult:
    def __init__(self, text, status_code=200, headers=None):
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}


class BaseCollector:
    def __init__(self, source_config):
        self.config = source_config
        self.source_id = source_config.get("id")
        self.source_name = source_config.get("name")
        self.source_url = source_config.get("url")
        self.sector = source_config.get("sector", "Central Government")
        self.category = source_config.get("category", "Central Govt")
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8"
        })

    def fetch_url(self, url, headers=None):
        """
        Politely fetches a URL with crawl delay and robust curl fallback for TLS compatibility.
        """
        time.sleep(REQUEST_INTERVAL_SECONDS)
        req_headers = dict(self.session.headers)
        if headers:
            req_headers.update(headers)

        # 1. Try requests.Session
        try:
            response = self.session.get(
                url,
                headers=req_headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
                verify=False
            )
            if response.status_code == 200 and len(response.text) > 200:
                return FetchResult(response.text, response.status_code, response.headers)
        except Exception as e:
            logger.debug(f"[{self.source_id}] Requests fetch failed for {url}: {e}. Attempting curl fallback...")

        # 2. Resilient fallback using system curl.exe (handles legacy government TLS handshakes)
        try:
            cmd = ["curl.exe", "-s", "-k", "-L", "-A", req_headers["User-Agent"], url]
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=REQUEST_TIMEOUT_SECONDS + 5)
            if res.returncode == 0 and len(res.stdout) > 200:
                logger.info(f"[{self.source_id}] Fetched {url} successfully via TLS-resilient fallback.")
                return FetchResult(res.stdout, 200, {})
        except Exception as ce:
            logger.warning(f"[{self.source_id}] Curl fallback also failed for {url}: {ce}")

        return None

    def collect(self):
        """
        Subclasses implement this to return a list of extracted notice dicts.
        """
        raise NotImplementedError("Subclasses must implement collect()")
