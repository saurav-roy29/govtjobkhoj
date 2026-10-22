"""
UPSC Collector
Extracts authentic recruitment notices, circulars, and advertisements directly from upsc.gov.in
"""

import re
import logging
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .base import BaseCollector

logger = logging.getLogger(__name__)


class UPSCCollector(BaseCollector):
    def collect(self):
        notices = []
        target_url = self.source_url or "https://www.upsc.gov.in/whats-new"
        response = self.fetch_url(target_url)
        if not response:
            logger.warning(f"Could not retrieve UPSC page: {target_url}")
            return notices

        soup = BeautifulSoup(response.text, "html.parser")
        seen_links = set()

        for a in soup.find_all("a"):
            txt = a.get_text(strip=True)
            href = a.get("href", "")

            if not href or href == "#" or len(txt) < 18:
                continue

            # Skip accessibility navigation, generic portal menus, and policy links
            skip_phrases = [
                "skip to", "accessibility", "screen reader", "website policy",
                "web information", "revised syllabus", "annual report", "citizen charter",
                "active examinations", "forthcoming examinations", "status of lateral recruitment",
                "online recruitment application (ora)", "status of recruitment cases",
                "forms for certificates", "recruitment tests", "recruitment requisition",
                "recruitment cases kept on hold", "representation on question papers",
                "the documentation page", "scheme and syllabus", "common mistakes",
                "helpline", "helpdesk", "government users", "forms & downloads",
                "annual calendar"
            ]
            if any(p in txt.lower() for p in skip_phrases):
                continue

            # Filter for recruitment, exam, post announcements, or advertisements
            recruitment_keywords = [
                "notice", "recruitment", "rectt", "posts of", "post of", "advertisement",
                "advt", "examination", "ldce", "cisf", "nda", "assistant director",
                "scientist", "medical officer", "provident fund"
            ]
            if not any(k in txt.lower() for k in recruitment_keywords):
                continue

            full_url = urljoin("https://www.upsc.gov.in", href)
            if full_url in seen_links:
                continue
            seen_links.add(full_url)

            # Extract vacancy count if mentioned in title (e.g., "74 Posts of...", "01 Post of...")
            vacancies = "Check Official Notice"
            vac_match = re.search(r'(\d+)\s+posts?', txt, re.IGNORECASE)
            if vac_match:
                vacancies = vac_match.group(1).lstrip("0") or vac_match.group(1)

            # Determine sub-organization from title
            org = "Union Public Service Commission (UPSC)"
            if "epfo" in txt.lower():
                org = "UPSC / Employees' Provident Fund Organisation (EPFO)"
            elif "ministry of defence" in txt.lower():
                org = "UPSC / Ministry of Defence"
            elif "ministry of home affairs" in txt.lower():
                org = "UPSC / Ministry of Home Affairs"
            elif "ministry of msme" in txt.lower():
                org = "UPSC / Ministry of MSME"
            elif "ministry of earth sciences" in txt.lower():
                org = "UPSC / Ministry of Earth Sciences"
            elif "gnctd" in txt.lower():
                org = "UPSC / Education Department, GNCTD"

            # Parse or assign publish date
            current_date_str = datetime.now().strftime("%Y-%m-%d")

            # Official links
            official_links = [
                {
                    "url": full_url,
                    "text": "Official Notification / Circular (PDF)" if full_url.endswith(".pdf") else "Official Commission Circular"
                },
                {
                    "url": "https://upsconline.nic.in/",
                    "text": "Official UPSC Online Portal (upsconline.nic.in)"
                }
            ]

            # Construct clean, structured content HTML
            content_html = f"""<h2 class="wp-block-heading">{txt}</h2>
<p><strong>Recruiting Authority:</strong> {org}<br>
<strong>Official Portal:</strong> <a href="https://www.upsc.gov.in" target="_blank" rel="noopener">upsc.gov.in</a> &bull; <a href="https://upsconline.nic.in" target="_blank" rel="noopener">upsconline.nic.in</a><br>
<strong>Total Vacancies:</strong> {vacancies}<br>
<strong>Application / Verification Mode:</strong> Online Official Commission Verification</p>

<h3 class="wp-block-heading">Recruitment Circular Summary</h3>
<p>The Union Public Service Commission (UPSC) has officially published the circular regarding <strong>{txt}</strong>. Candidates are required to download the authentic official notification circular and verify eligibility criteria, examination scheme, and guidelines directly from the authorized Commission portal.</p>

<h3 class="wp-block-heading">Authoritative Official Links</h3>
<ul class="wp-block-list">
<li><strong>Official Circular Document:</strong> <a href="{full_url}" target="_blank" rel="noopener">Click Here to View Official Notice</a></li>
<li><strong>UPSC Candidate Portal:</strong> <a href="https://upsconline.nic.in/" target="_blank" rel="noopener">Click Here for upsconline.nic.in</a></li>
</ul>
<p></p>"""

            notice_record = {
                "source_id": self.source_id,
                "title": txt,
                "org": org,
                "sector": "Central Government",
                "categories": ["Central Govt", "UPSC"],
                "vacancies": vacancies,
                "last_date": "Refer Official Circular",
                "publish_date": current_date_str,
                "app_mode": "Online",
                "status": "Open",
                "status_label": "Verified Active Notice",
                "qualification": "Graduate / Prescribed Qualifications",
                "official_links": official_links,
                "content_html": content_html,
                "source_url": full_url,
                "raw_url": full_url
            }
            notices.append(notice_record)

        logger.info(f"[{self.source_id}] Successfully extracted {len(notices)} notices from UPSC.")
        return notices
