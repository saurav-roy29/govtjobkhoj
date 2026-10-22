"""
Feed Collector
Generic collector supporting RSS, Atom, and JSON feeds for government portals.
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urljoin
from .base import BaseCollector

logger = logging.getLogger(__name__)


class FeedCollector(BaseCollector):
    def collect(self):
        notices = []
        if not self.source_url:
            return notices

        response = self.fetch_url(self.source_url)
        if not response:
            return notices

        content_type = response.headers.get("Content-Type", "").lower()
        if "json" in content_type:
            return self._parse_json(response.json())
        else:
            return self._parse_xml(response.text)

    def _parse_xml(self, xml_text):
        notices = []
        try:
            root = ET.fromstring(xml_text)
            # Find RSS items or Atom entries
            items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
            for item in items:
                title_el = item.find("title") or item.find("{http://www.w3.org/2005/Atom}title")
                link_el = item.find("link") or item.find("{http://www.w3.org/2005/Atom}link")
                date_el = item.find("pubDate") or item.find("{http://www.w3.org/2005/Atom}updated")

                title = title_el.text.strip() if title_el is not None and title_el.text else ""
                link = ""
                if link_el is not None:
                    link = link_el.get("href") or (link_el.text.strip() if link_el.text else "")

                if not title or not link:
                    continue

                pub_date = datetime.now().strftime("%Y-%m-%d")

                official_links = [
                    {"url": link, "text": "Official Notification / Circular"},
                    {"url": self.source_url, "text": f"Official {self.source_name} Source"}
                ]

                content_html = f"""<h2 class="wp-block-heading">{title}</h2>
<p><strong>Recruiting Authority:</strong> {self.source_name}<br>
<strong>Sector:</strong> {self.sector}<br>
<strong>Published:</strong> {pub_date}</p>
<p>Official circular retrieved from authorized portal feed. Verify application eligibility and deadlines directly at the source portal.</p>
<ul class="wp-block-list">
<li><strong>Official Circular:</strong> <a href="{link}" target="_blank" rel="noopener">Click Here to View Notice</a></li>
</ul>"""

                notices.append({
                    "source_id": self.source_id,
                    "title": title,
                    "org": self.source_name,
                    "sector": self.sector,
                    "categories": [self.category],
                    "vacancies": "Refer Official Circular",
                    "last_date": "Refer Official Circular",
                    "publish_date": pub_date,
                    "app_mode": "Online",
                    "status": "Open",
                    "status_label": "Verified Active Notice",
                    "qualification": "Prescribed Qualifications",
                    "official_links": official_links,
                    "content_html": content_html,
                    "source_url": link,
                    "raw_url": link
                })
        except Exception as e:
            logger.warning(f"[{self.source_id}] XML feed parse error: {e}")
        return notices

    def _parse_json(self, json_data):
        notices = []
        items = json_data if isinstance(json_data, list) else json_data.get("items", json_data.get("data", []))
        for item in items:
            title = item.get("title") or item.get("position_title")
            link = item.get("url") or item.get("link")
            if not title or not link:
                continue
            notices.append({
                "source_id": self.source_id,
                "title": title,
                "org": item.get("org") or self.source_name,
                "sector": self.sector,
                "categories": [self.category],
                "vacancies": str(item.get("vacancies", "Refer Notice")),
                "last_date": item.get("last_date", "Refer Notice"),
                "publish_date": datetime.now().strftime("%Y-%m-%d"),
                "app_mode": "Online",
                "status": "Open",
                "status_label": "Verified Active Notice",
                "qualification": item.get("qualification", "Refer Notice"),
                "official_links": [{"url": link, "text": "Official Notification"}],
                "content_html": f"<p>{title}</p>",
                "source_url": link,
                "raw_url": link
            })
        return notices
