"""
IBPS Collector
Extracts authentic public sector banking recruitments and official circulars directly from ibps.in
"""

import logging
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .base import BaseCollector

logger = logging.getLogger(__name__)


class IBPSCollector(BaseCollector):
    def collect(self):
        notices = []
        target_url = self.source_url or "https://www.ibps.in"
        response = self.fetch_url(target_url)
        if not response:
            logger.warning(f"Could not retrieve IBPS page: {target_url}")
            return notices

        soup = BeautifulSoup(response.text, "html.parser")
        seen_links = set()

        for a in soup.find_all("a"):
            txt = a.get_text(strip=True)
            href = a.get("href", "")

            if not href or href == "#" or len(txt) < 10:
                continue

            # Skip policy and non-recruitment links
            skip_phrases = ["policies", "rules & guidelines", "responsibility", "contact us", "overview", "tenders", "faq"]
            if any(p in txt.lower() for p in skip_phrases):
                continue

            # Filter for banking recruitment indicators
            recruitment_keywords = [
                "crp", "clerical", "csa", "po/mt", "specialist officer", "rrb",
                "recruitment", "banker faculty", "hindi officer", "call letter", "addendum"
            ]
            if not any(k in txt.lower() for k in recruitment_keywords):
                continue

            full_url = urljoin("https://www.ibps.in", href)
            if full_url in seen_links:
                continue
            seen_links.add(full_url)

            # Determine title formatting
            clean_title = txt
            if clean_title.startswith("CRP"):
                clean_title = f"IBPS {clean_title} Recruitment"
            elif not clean_title.lower().startswith("ibps"):
                clean_title = f"IBPS - {clean_title}"

            current_date_str = datetime.now().strftime("%Y-%m-%d")

            # Official links
            official_links = [
                {
                    "url": full_url,
                    "text": "Official IBPS Circular (PDF)" if full_url.endswith(".pdf") else "Official IBPS Recruitment Cadre Portal"
                },
                {
                    "url": "https://www.ibps.in",
                    "text": "Official IBPS Portal (ibps.in)"
                }
            ]

            # Construct clean structured content HTML
            content_html = f"""<h2 class="wp-block-heading">{clean_title}</h2>
<p><strong>Recruiting Organization:</strong> Institute of Banking Personnel Selection (IBPS)<br>
<strong>Official Portal:</strong> <a href="https://www.ibps.in" target="_blank" rel="noopener">ibps.in</a><br>
<strong>Sector:</strong> Public Sector Banking<br>
<strong>Application / Candidate Mode:</strong> Online Official Registration Portal</p>

<h3 class="wp-block-heading">Recruitment Notification Overview</h3>
<p>The Institute of Banking Personnel Selection (IBPS) has published official circular notifications regarding <strong>{clean_title}</strong> for candidate recruitments across participating nationalized and regional rural banks. Eligible applicants must review the detailed official brochure, educational requirements, age criteria, and participating bank vacancy schedules directly on the authorized IBPS website.</p>

<h3 class="wp-block-heading">Authorized Verification & Application Links</h3>
<ul class="wp-block-list">
<li><strong>Official Notification / Circular:</strong> <a href="{full_url}" target="_blank" rel="noopener">Click Here for Official IBPS Notification</a></li>
<li><strong>Authorized IBPS Homepage:</strong> <a href="https://www.ibps.in" target="_blank" rel="noopener">Click Here for ibps.in</a></li>
</ul>
<p></p>"""

            notice_record = {
                "source_id": self.source_id,
                "title": clean_title,
                "org": "Institute of Banking Personnel Selection (IBPS)",
                "sector": "Banking",
                "categories": ["Banks Job", "IBPS"],
                "vacancies": "Refer Official Circular",
                "last_date": "Refer Official Circular",
                "publish_date": current_date_str,
                "app_mode": "Online",
                "status": "Open",
                "status_label": "Verified Active Notice",
                "qualification": "Graduate / Prescribed Degrees",
                "official_links": official_links,
                "content_html": content_html,
                "source_url": full_url,
                "raw_url": full_url
            }
            notices.append(notice_record)

        logger.info(f"[{self.source_id}] Successfully extracted {len(notices)} notices from IBPS.")
        return notices
