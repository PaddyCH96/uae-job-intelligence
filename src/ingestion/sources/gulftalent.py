"""GulfTalent.com scraper for UAE AI & Data job postings."""

import hashlib
import random
import time
import urllib.robotparser
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.ingestion.base import BaseSource
from src.utils.logger import logger
from src.utils.text import clean_html, extract_salary_range, normalize_text


BASE_URL = "https://www.gulftalent.com"
JOBS_URL = f"{BASE_URL}/uae/jobs"

DEFAULT_KEYWORDS = [
    "data engineer",
    "data analyst",
    "machine learning",
    "AI engineer",
    "data scientist",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class GulfTalentSource(BaseSource):
    """Scraper for GulfTalent.com UAE data and AI job postings."""

    def __init__(self):
        super().__init__(source_name="GulfTalent", source_type="Scraper")
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
        self._robots_allowed = self._check_robots()

    # ------------------------------------------------------------------
    # robots.txt
    # ------------------------------------------------------------------

    def _check_robots(self) -> bool:
        """Return True if scraping the jobs path is allowed by robots.txt."""
        try:
            rp = urllib.robotparser.RobotFileParser()
            robots_url = f"{BASE_URL}/robots.txt"
            rp.set_url(robots_url)
            rp.read()
            allowed = rp.can_fetch("*", JOBS_URL)
            if not allowed:
                logger.warning(
                    "robots_disallowed",
                    source="GulfTalent",
                    url=JOBS_URL,
                )
            return allowed
        except Exception as exc:
            # Network error reading robots.txt — default to allowed but log it
            logger.warning(
                "robots_check_failed",
                source="GulfTalent",
                error=str(exc),
            )
            return True

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.HTTPError),
        reraise=True,
    )
    def _get(self, url: str, params: Optional[Dict] = None) -> requests.Response:
        """GET with retry on HTTP errors."""
        response = self._session.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response

    def _polite_sleep(self):
        time.sleep(random.uniform(1.0, 2.0))

    # ------------------------------------------------------------------
    # Listing page parsing
    # ------------------------------------------------------------------

    def _build_search_url(self, keyword: str, page: int) -> str:
        """Build a GulfTalent search URL for a given keyword and page."""
        slug = keyword.lower().replace(" ", "-")
        if page <= 1:
            return f"{BASE_URL}/uae/jobs/in-{slug}"
        return f"{BASE_URL}/uae/jobs/in-{slug}/page-{page}"

    def _parse_listing_page(self, html: str) -> List[Dict[str, Any]]:
        """Extract job stubs from a listing page."""
        soup = BeautifulSoup(html, "lxml")
        jobs: List[Dict[str, Any]] = []

        # GulfTalent wraps each job card in a <div class="job"> or similar
        # Use broad selectors so minor site changes don't break the whole scraper.
        cards = soup.select("div.job, article.job, li.job-item, div[class*='job-card']")

        if not cards:
            # Fallback: look for any <a> whose href contains /job/
            cards = soup.find_all("a", href=lambda h: h and "/job/" in h)
            for anchor in cards:
                href = anchor.get("href", "")
                url = urljoin(BASE_URL, href)
                title = normalize_text(anchor.get_text(strip=True)) or ""
                if title:
                    jobs.append({"url": url, "job_title": title})
            return jobs

        for card in cards:
            try:
                title_tag = card.select_one("h2, h3, .job-title, [class*='title']")
                title = title_tag.get_text(strip=True) if title_tag else ""

                link_tag = card.select_one("a[href*='/job/'], a[href*='/jobs/']")
                if not link_tag:
                    link_tag = card.select_one("a[href]")
                url = urljoin(BASE_URL, link_tag["href"]) if link_tag else ""

                company_tag = card.select_one(".company, .employer, [class*='company']")
                company = company_tag.get_text(strip=True) if company_tag else ""

                location_tag = card.select_one(".location, [class*='location'], [class*='city']")
                location = location_tag.get_text(strip=True) if location_tag else "UAE"

                salary_tag = card.select_one(".salary, [class*='salary']")
                salary_text = salary_tag.get_text(strip=True) if salary_tag else ""

                date_tag = card.select_one("time, .date, [class*='date'], [datetime]")
                posted_date = (
                    date_tag.get("datetime") or date_tag.get_text(strip=True)
                    if date_tag else ""
                )

                if title or url:
                    jobs.append({
                        "url": url,
                        "job_title": title,
                        "company": company,
                        "location": location,
                        "salary_raw": salary_text,
                        "posted_date": posted_date,
                    })
            except Exception as exc:
                logger.debug("card_parse_error", error=str(exc))
                continue

        return jobs

    # ------------------------------------------------------------------
    # Detail page parsing
    # ------------------------------------------------------------------

    def _parse_detail_page(self, html: str, stub: Dict[str, Any]) -> Dict[str, Any]:
        """Extract full job details from an individual job page."""
        soup = BeautifulSoup(html, "lxml")
        detail = dict(stub)

        # Description
        desc_tag = soup.select_one(
            ".job-description, #job-description, [class*='description'], article"
        )
        detail["description"] = clean_html(str(desc_tag)) if desc_tag else ""

        # Employment type
        for label in soup.find_all(string=lambda t: t and "employment type" in t.lower()):
            parent = label.find_parent()
            if parent:
                sibling = parent.find_next_sibling()
                if sibling:
                    detail["employment_type"] = sibling.get_text(strip=True)
                    break
        if "employment_type" not in detail:
            detail["employment_type"] = ""

        # Experience level
        for label in soup.find_all(string=lambda t: t and "experience" in t.lower()):
            parent = label.find_parent()
            if parent:
                sibling = parent.find_next_sibling()
                if sibling:
                    detail["experience_level"] = sibling.get_text(strip=True)
                    break
        if "experience_level" not in detail:
            detail["experience_level"] = ""

        # Visa / sponsorship
        full_text = soup.get_text(" ", strip=True).lower()
        detail["visa_sponsorship"] = any(
            kw in full_text
            for kw in ("visa sponsorship", "visa provided", "work permit")
        )

        # Remote
        detail["remote_allowed"] = any(
            kw in full_text
            for kw in ("remote", "work from home", "wfh", "hybrid")
        )

        # Salary from detail page if not already captured
        if not detail.get("salary_raw"):
            salary_tag = soup.select_one(".salary, [class*='salary']")
            detail["salary_raw"] = salary_tag.get_text(strip=True) if salary_tag else ""

        return detail

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def fetch_jobs(self, keywords: Optional[List[str]] = None, max_pages: int = 3) -> List[Dict[str, Any]]:
        """
        Scrape GulfTalent for UAE data/AI job listings.

        Args:
            keywords: Search keywords; defaults to DEFAULT_KEYWORDS.
            max_pages: Maximum listing pages to scrape per keyword.

        Returns:
            List of raw job dicts ready for transform_job().
        """
        if not self._robots_allowed:
            self.logger.warning("scraping_skipped_robots", url=JOBS_URL)
            return []

        search_keywords = keywords or DEFAULT_KEYWORDS
        seen_urls: set = set()
        all_jobs: List[Dict[str, Any]] = []

        for keyword in search_keywords:
            self.logger.info("keyword_search_started", keyword=keyword)
            for page in range(1, max_pages + 1):
                url = self._build_search_url(keyword, page)
                try:
                    self._polite_sleep()
                    response = self._get(url)
                    stubs = self._parse_listing_page(response.text)

                    if not stubs:
                        self.logger.info("no_more_results", keyword=keyword, page=page)
                        break

                    for stub in stubs:
                        job_url = stub.get("url", "")
                        if not job_url or job_url in seen_urls:
                            continue
                        seen_urls.add(job_url)

                        # Fetch detail page
                        try:
                            self._polite_sleep()
                            detail_resp = self._get(job_url)
                            full_job = self._parse_detail_page(detail_resp.text, stub)
                        except Exception as detail_exc:
                            self.logger.warning(
                                "detail_page_failed",
                                url=job_url,
                                error=str(detail_exc),
                            )
                            full_job = stub

                        all_jobs.append(full_job)

                except requests.HTTPError as http_err:
                    self.logger.error(
                        "listing_page_http_error",
                        keyword=keyword,
                        page=page,
                        error=str(http_err),
                    )
                    break
                except Exception as exc:
                    self.logger.error(
                        "listing_page_error",
                        keyword=keyword,
                        page=page,
                        error=str(exc),
                    )
                    break

        self.logger.info("fetch_total", count=len(all_jobs))
        return all_jobs

    # ------------------------------------------------------------------
    # Transformation
    # ------------------------------------------------------------------

    def _generate_source_id(self, raw_job: Dict[str, Any]) -> str:
        """Use the job URL as a stable unique identifier."""
        url = raw_job.get("url", "")
        id_string = f"GulfTalent_{url}"
        return hashlib.md5(id_string.encode()).hexdigest()

    def transform_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a raw GulfTalent job dict into the standardised schema."""
        salary_raw = raw_job.get("salary_raw", "") or ""
        try:
            salary_range = extract_salary_range(salary_raw)
        except Exception:
            salary_range = salary_raw or None

        raw_data: Dict[str, Any] = {
            "job_title": raw_job.get("job_title", ""),
            "company": raw_job.get("company", ""),
            "location": raw_job.get("location", "UAE"),
            "description": raw_job.get("description", ""),
            "salary_range": salary_range,
            "remote_allowed": bool(raw_job.get("remote_allowed", False)),
            "visa_sponsorship": bool(raw_job.get("visa_sponsorship", False)),
            "url": raw_job.get("url", ""),
            "posted_date": raw_job.get("posted_date", ""),
            "employment_type": raw_job.get("employment_type", ""),
            "experience_level": raw_job.get("experience_level", ""),
        }

        return {
            "source_id": self._generate_source_id(raw_job),
            "source_name": self.source_name,
            "raw_data": raw_data,
            "ingested_at": datetime.now(UTC).isoformat(),
        }
