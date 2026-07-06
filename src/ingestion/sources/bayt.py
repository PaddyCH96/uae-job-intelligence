"""Bayt.com scraper source for UAE AI & Data jobs.

Scrapes publicly accessible job listings from bayt.com/en/uae/jobs/ for
data and AI roles. Respects robots.txt, rate-limits requests, and never
stores applicant profile data.
"""

from __future__ import annotations

import hashlib
import random
import re
import time
from datetime import datetime, UTC, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)
import logging

from src.ingestion.base import BaseSource
from src.utils.logger import logger
from src.utils.text import clean_html, normalize_text, extract_salary_range

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://www.bayt.com"
JOBS_BASE = "https://www.bayt.com/en/uae/jobs/"
ROBOTS_URL = "https://www.bayt.com/robots.txt"

DEFAULT_SEARCH_TERMS = [
    "data-engineer",
    "data-analyst",
    "machine-learning",
    "ai-engineer",
    "data-scientist",
]

# Bayt encodes search keywords into URL path segments, e.g.
# /en/uae/jobs/data-engineer-jobs/
SEARCH_PATH_TEMPLATE = "/en/uae/jobs/{keyword}-jobs/"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Employment type normalisation map
EMPLOYMENT_TYPE_MAP = {
    "full time": "Full-time",
    "full-time": "Full-time",
    "part time": "Part-time",
    "part-time": "Part-time",
    "contract": "Contract",
    "temporary": "Temporary",
    "freelance": "Freelance",
    "internship": "Internship",
}

# Experience level keywords
EXPERIENCE_PATTERNS = [
    (r"(\d+)\s*\+?\s*years?\s+of\s+experience", None),  # captured below
    (r"entry.level|fresher|graduate|junior|0[\s-]+[12]\s*year", "Entry Level"),
    (r"mid.level|2[\s-]+5\s*year|intermediate", "Mid Level"),
    (r"senior|lead|principal|staff|6\+|7\+|8\+|9\+|10\+", "Senior Level"),
    (r"manager|director|head\s+of|vp\b|c-suite|cto|cdo", "Manager/Director"),
]


# ---------------------------------------------------------------------------
# Retry decorator (module-level so it can be reused for any request helper)
# ---------------------------------------------------------------------------

def _retry_decorator():
    """Return a tenacity retry decorator configured for HTTP requests."""
    return retry(
        retry=retry_if_exception_type((requests.RequestException, OSError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=16),
        before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
        reraise=True,
    )


# ---------------------------------------------------------------------------
# BaytSource
# ---------------------------------------------------------------------------

class BaytSource(BaseSource):
    """Scraper for Bayt.com UAE job listings.

    Scrapes the public job search pages only — no login required, no
    applicant profile data collected.
    """

    def __init__(self) -> None:
        super().__init__(source_name="Bayt", source_type="Scraper")
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
        self._robots: Optional[RobotFileParser] = None
        self._robots_loaded = False

    # ------------------------------------------------------------------
    # Robots.txt compliance
    # ------------------------------------------------------------------

    def _load_robots(self) -> None:
        """Fetch and parse robots.txt once per session."""
        if self._robots_loaded:
            return
        parser = RobotFileParser()
        parser.set_url(ROBOTS_URL)
        try:
            parser.read()
            self._robots = parser
            self.logger.info("robots_loaded", url=ROBOTS_URL)
        except Exception as exc:
            # If we cannot fetch robots.txt, be conservative: block all
            self.logger.warning("robots_fetch_failed", error=str(exc))
            self._robots = None
        finally:
            self._robots_loaded = True

    def _is_allowed(self, url: str) -> bool:
        """Return True if robots.txt permits fetching *url*."""
        self._load_robots()
        if self._robots is None:
            # Could not load robots — be conservative and disallow
            return False
        return self._robots.can_fetch(USER_AGENT, url)

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _get(self, url: str) -> Optional[requests.Response]:
        """GET *url* with retry, rate-limit delay, and error handling.

        Returns the Response on 2xx, or None on any error.
        """
        if not self._is_allowed(url):
            self.logger.warning("robots_disallowed", url=url)
            return None

        # Rate-limit: sleep 1-2 s before every outbound request
        time.sleep(random.uniform(1.0, 2.0))

        @_retry_decorator()
        def _fetch() -> requests.Response:
            resp = self._session.get(url, timeout=15)
            resp.raise_for_status()
            return resp

        try:
            return _fetch()
        except requests.HTTPError as exc:
            self.logger.error("http_error", url=url, status=exc.response.status_code if exc.response is not None else "?")
            return None
        except Exception as exc:
            self.logger.error("request_failed", url=url, error=str(exc))
            return None

    # ------------------------------------------------------------------
    # Listing page scraping
    # ------------------------------------------------------------------

    def _listing_url(self, keyword: str, page: int) -> str:
        """Build Bayt listing URL for *keyword* and *page* number."""
        path = SEARCH_PATH_TEMPLATE.format(keyword=keyword)
        if page > 1:
            # Bayt uses ?page=N query string for pagination
            return f"{BASE_URL}{path}?page={page}"
        return f"{BASE_URL}{path}"

    def _scrape_listing_page(self, url: str) -> tuple[List[str], bool]:
        """Scrape one listing page.

        Returns:
            (job_detail_urls, has_next_page)
        """
        resp = self._get(url)
        if resp is None:
            return [], False

        soup = BeautifulSoup(resp.text, "lxml")

        # Job cards — Bayt wraps each card in <li> inside #results_list or
        # similar containers. We cast a wide net and deduplicate.
        job_urls: List[str] = []

        # Primary selector: article/li cards that contain a job-link
        for tag in soup.select("li[data-job-id], li.has-pointer"):
            link = tag.find("a", href=re.compile(r"/en/uae/jobs/.*-job-"))
            if link and link.get("href"):
                href = link["href"]
                full_url = urljoin(BASE_URL, href)
                if full_url not in job_urls:
                    job_urls.append(full_url)

        # Fallback: all links matching the detail URL pattern
        if not job_urls:
            for link in soup.find_all("a", href=re.compile(r"/en/[a-z]{2}/jobs/.+-job-\d+")):
                href = link["href"]
                full_url = urljoin(BASE_URL, href)
                if full_url not in job_urls:
                    job_urls.append(full_url)

        # Detect next page — look for a "Next" pagination link
        has_next = False
        next_link = soup.find("a", string=re.compile(r"next|»", re.I))
        if next_link and next_link.get("href"):
            has_next = True
        else:
            # Alternative: rel="next"
            next_rel = soup.find("a", rel="next")
            if next_rel:
                has_next = True

        self.logger.info("listing_scraped", url=url, jobs_found=len(job_urls), has_next=has_next)
        return job_urls, has_next

    # ------------------------------------------------------------------
    # Detail page scraping
    # ------------------------------------------------------------------

    def _scrape_detail_page(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape a single job detail page and return a raw dict."""
        resp = self._get(url)
        if resp is None:
            return None

        soup = BeautifulSoup(resp.text, "lxml")

        raw: Dict[str, Any] = {"url": url}

        # ---- Job title ----
        title_el = (
            soup.find("h1")
            or soup.find("h2", class_=re.compile(r"title|job", re.I))
        )
        raw["job_title"] = title_el.get_text(strip=True) if title_el else ""

        # ---- Company ----
        company_el = soup.find(
            ["span", "a", "div"],
            class_=re.compile(r"company|employer|firm", re.I),
        )
        if not company_el:
            # Try itemprop
            company_el = soup.find(attrs={"itemprop": "hiringOrganization"})
        raw["company"] = company_el.get_text(strip=True) if company_el else ""

        # ---- Location ----
        location_el = soup.find(
            ["span", "div"],
            class_=re.compile(r"location|city|country", re.I),
        )
        if not location_el:
            location_el = soup.find(attrs={"itemprop": "jobLocation"})
        raw["location"] = _extract_uae_city(
            location_el.get_text(strip=True) if location_el else ""
        )

        # ---- Description ----
        desc_el = (
            soup.find("div", class_=re.compile(r"description|job-desc|content", re.I))
            or soup.find("section", class_=re.compile(r"description|job-desc", re.I))
            or soup.find(attrs={"itemprop": "description"})
        )
        raw["description"] = clean_html(str(desc_el)) if desc_el else ""

        # ---- Salary ----
        salary_el = soup.find(
            ["span", "div"],
            class_=re.compile(r"salary|compensation|remuneration", re.I),
        )
        raw["salary_range"] = salary_el.get_text(strip=True) if salary_el else ""

        # ---- Employment type ----
        emp_el = soup.find(
            ["span", "div", "li"],
            class_=re.compile(r"employment.type|job.type|work.type", re.I),
        )
        raw["employment_type"] = emp_el.get_text(strip=True) if emp_el else ""

        # ---- Posted date ----
        date_el = (
            soup.find("time")
            or soup.find(attrs={"itemprop": "datePosted"})
            or soup.find(["span", "div"], class_=re.compile(r"date|posted|ago", re.I))
        )
        raw["posted_date"] = _parse_date(
            date_el.get("datetime") or date_el.get_text(strip=True)
            if date_el else ""
        )

        # ---- Remote ----
        page_text = soup.get_text(" ", strip=True).lower()
        raw["remote_allowed"] = bool(
            re.search(r"\bremote\b|\bwork from home\b|\bwfh\b", page_text)
        )

        # ---- Visa sponsorship ----
        raw["visa_sponsorship"] = bool(
            re.search(r"\bvisa\s+sponsor(ship|ed)?\b|\brelocation\s+package\b", page_text)
        )

        # ---- Experience level ----
        raw["experience_level"] = _infer_experience_level(page_text)

        self.logger.debug("detail_scraped", url=url, title=raw.get("job_title"))
        return raw

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_jobs(
        self,
        keywords: Optional[List[str]] = None,
        max_pages: int = 3,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Scrape Bayt.com UAE job listings for AI/data roles.

        Args:
            keywords: Search keywords (defaults to DEFAULT_SEARCH_TERMS).
            max_pages: Maximum listing pages to scrape per keyword.

        Returns:
            List of raw job dicts ready for transform_job().
        """
        terms = keywords or DEFAULT_SEARCH_TERMS
        seen_urls: set[str] = set()
        all_jobs: List[Dict[str, Any]] = []

        for keyword in terms:
            self.logger.info("keyword_start", keyword=keyword)

            for page in range(1, max_pages + 1):
                listing_url = self._listing_url(keyword, page)
                job_urls, has_next = self._scrape_listing_page(listing_url)

                for job_url in job_urls:
                    if job_url in seen_urls:
                        continue
                    seen_urls.add(job_url)

                    raw = self._scrape_detail_page(job_url)
                    if raw:
                        all_jobs.append(raw)

                if not has_next or page >= max_pages:
                    break

            self.logger.info("keyword_done", keyword=keyword, total_so_far=len(all_jobs))

        self.logger.info("fetch_jobs_complete", total=len(all_jobs))
        return all_jobs

    # ------------------------------------------------------------------
    # Transform & ID
    # ------------------------------------------------------------------

    def _generate_source_id(self, raw_job: Dict[str, Any]) -> str:
        """Use the Bayt job URL as the stable unique identifier."""
        url = raw_job.get("url", "")
        if not url:
            # Fallback: hash title + company
            fallback = f"Bayt_{raw_job.get('job_title', '')}_{raw_job.get('company', '')}"
            return hashlib.md5(fallback.encode()).hexdigest()
        return hashlib.md5(f"Bayt_{url}".encode()).hexdigest()

    def transform_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """Map scraped fields to the standard platform schema."""
        salary_text = raw_job.get("salary_range", "")
        # Also search description for salary if not found in dedicated field
        if not salary_text:
            salary_text = raw_job.get("description", "")

        salary_min, salary_max, currency = extract_salary_range(salary_text)
        salary_range_str = (
            f"{currency} {salary_min:,.0f} - {salary_max:,.0f}"
            if salary_min and salary_max
            else raw_job.get("salary_range", "")
        )

        normalized_raw = {
            "job_title": raw_job.get("job_title", "").strip(),
            "company": raw_job.get("company", "").strip(),
            "location": raw_job.get("location", "UAE"),
            "description": raw_job.get("description", ""),
            "salary_range": salary_range_str,
            "remote_allowed": bool(raw_job.get("remote_allowed", False)),
            "visa_sponsorship": bool(raw_job.get("visa_sponsorship", False)),
            "url": raw_job.get("url", ""),
            "posted_date": raw_job.get("posted_date", ""),
            "employment_type": _normalise_employment_type(
                raw_job.get("employment_type", "")
            ),
            "experience_level": raw_job.get("experience_level", ""),
        }

        return {
            "source_id": self._generate_source_id(raw_job),
            "source_name": self.source_name,
            "raw_data": normalized_raw,
            "ingested_at": datetime.now(UTC).isoformat(),
        }


# ---------------------------------------------------------------------------
# Module-level helpers (pure functions — no I/O, easily unit-tested)
# ---------------------------------------------------------------------------

_UAE_CITIES = [
    "Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Fujairah",
    "Ras Al Khaimah", "Umm Al Quwain", "Al Ain",
]


def _extract_uae_city(text: str) -> str:
    """Return the first UAE city found in *text*, else the text itself (or 'UAE')."""
    if not text:
        return "UAE"
    for city in _UAE_CITIES:
        if city.lower() in text.lower():
            return city
    # Return the raw location string (trimmed) if no known city found
    cleaned = text.strip()
    return cleaned if cleaned else "UAE"


def _parse_date(raw: str) -> str:
    """Best-effort ISO-8601 date string from *raw* text.

    Handles:
    - ISO strings already ("2024-05-01", "2024-05-01T12:00:00Z")
    - Relative strings ("2 days ago", "1 week ago", "1 month ago")
    Returns empty string on failure.
    """
    if not raw:
        return ""
    raw = raw.strip()

    # Already ISO-ish?
    iso_match = re.match(r"(\d{4}-\d{2}-\d{2})", raw)
    if iso_match:
        return iso_match.group(1)

    now = datetime.now(UTC)

    # "N days/weeks/months ago"
    relative = re.search(
        r"(\d+)\s+(day|week|month|hour|minute)s?\s+ago", raw, re.I
    )
    if relative:
        n = int(relative.group(1))
        unit = relative.group(2).lower()
        delta_map = {
            "minute": timedelta(minutes=n),
            "hour": timedelta(hours=n),
            "day": timedelta(days=n),
            "week": timedelta(weeks=n),
            "month": timedelta(days=n * 30),
        }
        dt = now - delta_map.get(unit, timedelta(0))
        return dt.date().isoformat()

    # "Today" / "Yesterday"
    if re.search(r"\btoday\b", raw, re.I):
        return now.date().isoformat()
    if re.search(r"\byesterday\b", raw, re.I):
        return (now - timedelta(days=1)).date().isoformat()

    return ""


def _normalise_employment_type(raw: str) -> str:
    """Map a raw employment type string to a canonical value."""
    if not raw:
        return ""
    key = raw.strip().lower()
    for pattern, canonical in EMPLOYMENT_TYPE_MAP.items():
        if pattern in key:
            return canonical
    return raw.strip()


def _infer_experience_level(page_text: str) -> str:
    """Infer experience level from lowercase *page_text*."""
    for pattern, label in EXPERIENCE_PATTERNS:
        if label is None:
            # Year-count pattern — map to a level
            m = re.search(pattern, page_text, re.I)
            if m:
                years = int(m.group(1))
                if years <= 2:
                    return "Entry Level"
                elif years <= 5:
                    return "Mid Level"
                else:
                    return "Senior Level"
        else:
            if re.search(pattern, page_text, re.I):
                return label
    return ""
