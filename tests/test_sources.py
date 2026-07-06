"""Tests for the three real scraper sources: Bayt, GulfTalent, NaukriGulf.

All HTTP calls are mocked — no live network traffic in this suite.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.ingestion.sources.bayt import (
    BaytSource,
    _parse_date,
    _extract_uae_city,
    _normalise_employment_type,
    _infer_experience_level,
)
from src.ingestion.sources.gulftalent import GulfTalentSource
from src.ingestion.sources.naukrigulf import NaukriGulfSource


# ---------------------------------------------------------------------------
# Minimal HTML fixtures (inline — no live network required)
# ---------------------------------------------------------------------------

# Bayt listing page — uses the fallback anchor selector pattern
BAYT_LISTING_HTML = """\
<!DOCTYPE html><html><body>
  <h1>Data Jobs in UAE</h1>
  <a href="/en/uae/jobs/data-engineer-job-99001">Data Engineer - Acme Corp</a>
  <a href="/en/ae/jobs/data-analyst-job-99002">Data Analyst - Beta Ltd</a>
  <a href="/unrelated-link">Not a job</a>
</body></html>
"""

# Bayt detail page
BAYT_DETAIL_HTML = """\
<!DOCTYPE html><html><body>
  <h1>Data Engineer</h1>
  <span class="company">Acme Corp Dubai</span>
  <span class="location">Dubai, UAE</span>
  <div class="description">
    Build data pipelines in Python and SQL.
    Remote-friendly. AED 25,000 per month.
    Visa sponsorship available.
    3+ years of experience required.
  </div>
  <span class="salary">AED 20,000 - 30,000</span>
  <time datetime="2026-07-01">July 1 2026</time>
</body></html>
"""

# GulfTalent listing page — fallback anchor path with /job/ in href
GULFTALENT_LISTING_HTML = """\
<!DOCTYPE html><html><body>
  <h2>UAE Data Jobs</h2>
  <a href="/job/data-engineer-acme-123">Data Engineer at Acme</a>
  <a href="/job/ml-engineer-beta-456">ML Engineer at Beta</a>
</body></html>
"""

# GulfTalent detail page
GULFTALENT_DETAIL_HTML = """\
<!DOCTYPE html><html><body>
  <h1>Data Engineer</h1>
  <div class="company">Acme Corp</div>
  <div class="location">Dubai</div>
  <div class="job-description">
    Build ETL pipelines. Hybrid remote.
    Visa sponsorship provided. Full time role.
    AED 22,000 - 28,000 per month.
  </div>
  <span class="salary">AED 22,000 - 28,000</span>
  <time datetime="2026-07-02">2026-07-02</time>
</body></html>
"""

# NaukriGulf listing page — fallback anchor with /jobs/ in href
NAUKRIGULF_LISTING_HTML = """\
<!DOCTYPE html><html><body>
  <h2>Data Jobs UAE</h2>
  <a href="/jobs/data-engineer-dubai-789">Data Engineer Dubai</a>
  <a href="/jobs/ai-engineer-abu-dhabi-101">AI Engineer Abu Dhabi</a>
</body></html>
"""

# NaukriGulf detail page
NAUKRIGULF_DETAIL_HTML = """\
<!DOCTYPE html><html><body>
  <h1>Data Engineer</h1>
  <div class="company-name">Tech Solutions LLC</div>
  <div class="location">Dubai</div>
  <div class="job-description">
    Full time position. 5+ years experience.
    Remote work from home option. Visa provided.
    AED 18,000 - 24,000/month.
  </div>
  <span class="salary">AED 18,000 - 24,000</span>
  <time datetime="2026-07-03">2026-07-03</time>
</body></html>
"""

# ---------------------------------------------------------------------------
# Shared raw job dicts used across source tests
# ---------------------------------------------------------------------------

RAW_JOB_BAYT = {
    "url": "https://www.bayt.com/en/uae/jobs/data-engineer-job-99001",
    "job_title": "Data Engineer",
    "company": "Acme Corp",
    "location": "Dubai",
    "description": "Build data pipelines. Python, SQL required.",
    "salary_range": "AED 20,000 - 30,000",
    "employment_type": "Full-time",
    "remote_allowed": True,
    "visa_sponsorship": False,
    "posted_date": "2026-07-01",
    "experience_level": "Mid Level",
}

RAW_JOB_GULFTALENT = {
    "url": "https://www.gulftalent.com/job/data-engineer-acme-123",
    "job_title": "Data Engineer",
    "company": "Acme Corp",
    "location": "Dubai",
    "description": "ETL pipelines. Python required.",
    "salary_raw": "AED 22,000 - 28,000",
    "employment_type": "Full-time",
    "remote_allowed": False,
    "visa_sponsorship": True,
    "posted_date": "2026-07-02",
    "experience_level": "Senior Level",
}

RAW_JOB_NAUKRIGULF = {
    "url": "https://www.naukrigulf.com/jobs/data-engineer-dubai-789",
    "job_title": "Data Engineer",
    "company": "Tech Solutions LLC",
    "location": "Dubai",
    "description": "Full-time data engineering role.",
    "salary_raw": "AED 18,000 - 24,000",
    "employment_type": "Full-time",
    "remote_allowed": True,
    "visa_sponsorship": False,
    "posted_date": "2026-07-03",
    "experience_level": "Mid Level",
}

REQUIRED_RAW_DATA_KEYS = {
    "job_title", "company", "location", "description",
    "salary_range", "remote_allowed", "visa_sponsorship",
    "url", "posted_date", "employment_type", "experience_level",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def bayt_source():
    """BaytSource with robots-check bypassed (no network call at init)."""
    src = BaytSource()
    # Pre-seed lazy robots state so _is_allowed() never touches the network
    src._robots_loaded = True
    src._robots = MagicMock()
    src._robots.can_fetch.return_value = True
    return src


@pytest.fixture
def gulftalent_source():
    """GulfTalentSource with robots check patched to True during __init__."""
    with patch(
        "src.ingestion.sources.gulftalent.urllib.robotparser.RobotFileParser"
    ) as mock_rfp:
        mock_rfp.return_value.can_fetch.return_value = True
        src = GulfTalentSource()
    return src


@pytest.fixture
def naukrigulf_source():
    """NaukriGulfSource with robots check patched to True during __init__."""
    with patch(
        "src.ingestion.sources.naukrigulf.urllib.robotparser.RobotFileParser"
    ) as mock_rfp:
        mock_rfp.return_value.can_fetch.return_value = True
        src = NaukriGulfSource()
    return src


def _mock_response(html: str) -> MagicMock:
    """Return a minimal mock Response object with the given HTML body."""
    resp = MagicMock()
    resp.text = html
    resp.raise_for_status = MagicMock()
    return resp


# ===========================================================================
# BaytSource tests
# ===========================================================================


class TestBaytSource:

    def test_instantiation(self, bayt_source):
        assert bayt_source.source_name == "Bayt"
        assert bayt_source.source_type == "Scraper"

    def test_transform_job_maps_all_required_fields(self, bayt_source):
        result = bayt_source.transform_job(RAW_JOB_BAYT)

        assert "source_id" in result and result["source_id"]
        assert result["source_name"] == "Bayt"
        assert "ingested_at" in result
        assert isinstance(result["ingested_at"], str)
        datetime.fromisoformat(result["ingested_at"])

        raw = result["raw_data"]
        assert REQUIRED_RAW_DATA_KEYS == set(raw.keys())

    def test_transform_job_copies_core_fields(self, bayt_source):
        result = bayt_source.transform_job(RAW_JOB_BAYT)
        raw = result["raw_data"]
        assert raw["job_title"] == "Data Engineer"
        assert raw["company"] == "Acme Corp"
        assert raw["location"] == "Dubai"
        assert raw["remote_allowed"] is True
        assert raw["visa_sponsorship"] is False

    def test_transform_job_source_id_is_deterministic(self, bayt_source):
        id1 = bayt_source.transform_job(RAW_JOB_BAYT)["source_id"]
        id2 = bayt_source.transform_job(RAW_JOB_BAYT)["source_id"]
        assert id1 == id2

    def test_transform_job_different_urls_produce_different_ids(self, bayt_source):
        job_a = dict(RAW_JOB_BAYT, url="https://www.bayt.com/en/uae/jobs/job-aaa")
        job_b = dict(RAW_JOB_BAYT, url="https://www.bayt.com/en/uae/jobs/job-bbb")
        assert bayt_source.transform_job(job_a)["source_id"] != bayt_source.transform_job(job_b)["source_id"]

    def test_validate_job_passes_valid_job(self, bayt_source):
        transformed = bayt_source.transform_job(RAW_JOB_BAYT)
        assert bayt_source.validate_job(transformed) is True

    def test_validate_job_fails_missing_title(self, bayt_source):
        job = {
            "source_id": "abc123",
            "source_name": "Bayt",
            "raw_data": {"job_title": "", "company": "Acme"},
        }
        assert bayt_source.validate_job(job) is False

    def test_validate_job_fails_missing_source_id(self, bayt_source):
        job = {
            "source_name": "Bayt",
            "raw_data": {"job_title": "Data Engineer"},
        }
        assert bayt_source.validate_job(job) is False

    def test_validate_job_accepts_title_alias(self, bayt_source):
        job = {
            "source_id": "abc123",
            "source_name": "Bayt",
            "raw_data": {"title": "Data Engineer"},
        }
        assert bayt_source.validate_job(job) is True

    def test_fetch_jobs_returns_list_of_dicts(self, bayt_source):
        listing_resp = _mock_response(BAYT_LISTING_HTML)
        detail_resp = _mock_response(BAYT_DETAIL_HTML)

        with patch("time.sleep"), \
             patch.object(
                 bayt_source._session, "get",
                 side_effect=[listing_resp, detail_resp, detail_resp],
             ):
            jobs = bayt_source.fetch_jobs(keywords=["data-engineer"], max_pages=1)

        assert isinstance(jobs, list)
        assert len(jobs) >= 1
        assert "job_title" in jobs[0]
        assert "url" in jobs[0]

    def test_fetch_jobs_deduplicates_urls(self, bayt_source):
        """Same job URL across keyword searches returned only once."""
        listing_resp = _mock_response(BAYT_LISTING_HTML)
        detail_resp = _mock_response(BAYT_DETAIL_HTML)

        with patch("time.sleep"), \
             patch.object(
                 bayt_source._session, "get",
                 side_effect=[
                     listing_resp, detail_resp, detail_resp,  # keyword 1
                     listing_resp,                             # keyword 2 (same URLs already seen)
                 ],
             ):
            jobs = bayt_source.fetch_jobs(
                keywords=["data-engineer", "data-engineer"], max_pages=1
            )

        urls = [j.get("url") for j in jobs if j.get("url")]
        assert len(urls) == len(set(urls)), "Duplicate URLs slipped through"

    def test_robots_disallowed_returns_empty(self, bayt_source):
        bayt_source._robots.can_fetch.return_value = False
        with patch("time.sleep"):
            jobs = bayt_source.fetch_jobs(keywords=["data-engineer"], max_pages=1)
        assert jobs == []

    def test_http_error_resilience_does_not_raise(self, bayt_source):
        """If HTTP fails, fetch_jobs returns [] and never raises."""
        with patch("time.sleep"), \
             patch.object(
                 bayt_source._session, "get",
                 side_effect=requests.exceptions.ConnectionError("refused"),
             ):
            jobs = bayt_source.fetch_jobs(keywords=["data-engineer"], max_pages=1)

        assert isinstance(jobs, list)


# ===========================================================================
# GulfTalentSource tests
# ===========================================================================


class TestGulfTalentSource:

    def test_instantiation(self, gulftalent_source):
        assert gulftalent_source.source_name == "GulfTalent"
        assert gulftalent_source.source_type == "Scraper"

    def test_robots_allowed_is_true_on_happy_init(self, gulftalent_source):
        assert gulftalent_source._robots_allowed is True

    def test_transform_job_maps_all_required_fields(self, gulftalent_source):
        result = gulftalent_source.transform_job(RAW_JOB_GULFTALENT)

        assert "source_id" in result and result["source_id"]
        assert result["source_name"] == "GulfTalent"
        assert "ingested_at" in result
        datetime.fromisoformat(result["ingested_at"])

        raw = result["raw_data"]
        assert REQUIRED_RAW_DATA_KEYS == set(raw.keys())

    def test_transform_job_copies_core_fields(self, gulftalent_source):
        result = gulftalent_source.transform_job(RAW_JOB_GULFTALENT)
        raw = result["raw_data"]
        assert raw["job_title"] == "Data Engineer"
        assert raw["company"] == "Acme Corp"
        assert raw["location"] == "Dubai"
        assert raw["remote_allowed"] is False
        assert raw["visa_sponsorship"] is True

    def test_transform_job_source_id_is_deterministic(self, gulftalent_source):
        id1 = gulftalent_source.transform_job(RAW_JOB_GULFTALENT)["source_id"]
        id2 = gulftalent_source.transform_job(RAW_JOB_GULFTALENT)["source_id"]
        assert id1 == id2

    def test_validate_job_passes_valid_job(self, gulftalent_source):
        transformed = gulftalent_source.transform_job(RAW_JOB_GULFTALENT)
        assert gulftalent_source.validate_job(transformed) is True

    def test_validate_job_fails_missing_title(self, gulftalent_source):
        job = {
            "source_id": "xyz",
            "source_name": "GulfTalent",
            "raw_data": {"job_title": "", "company": "Corp"},
        }
        assert gulftalent_source.validate_job(job) is False

    def test_validate_job_fails_missing_source_id(self, gulftalent_source):
        job = {
            "source_name": "GulfTalent",
            "raw_data": {"job_title": "ML Engineer"},
        }
        assert gulftalent_source.validate_job(job) is False

    def test_fetch_jobs_returns_list_of_dicts(self, gulftalent_source):
        listing_resp = _mock_response(GULFTALENT_LISTING_HTML)
        detail_resp = _mock_response(GULFTALENT_DETAIL_HTML)

        with patch("time.sleep"), \
             patch.object(
                 gulftalent_source._session, "get",
                 side_effect=[listing_resp, detail_resp, detail_resp],
             ):
            jobs = gulftalent_source.fetch_jobs(keywords=["data engineer"], max_pages=1)

        assert isinstance(jobs, list)
        assert len(jobs) >= 1
        assert "job_title" in jobs[0]

    def test_robots_disallowed_returns_empty(self):
        with patch(
            "src.ingestion.sources.gulftalent.urllib.robotparser.RobotFileParser"
        ) as mock_rfp:
            mock_rfp.return_value.can_fetch.return_value = False
            src = GulfTalentSource()

        assert src._robots_allowed is False
        jobs = src.fetch_jobs(keywords=["data engineer"], max_pages=1)
        assert jobs == []

    def test_http_error_resilience_does_not_raise(self, gulftalent_source):
        with patch("time.sleep"), \
             patch.object(
                 gulftalent_source._session, "get",
                 side_effect=requests.exceptions.ConnectionError("timeout"),
             ):
            jobs = gulftalent_source.fetch_jobs(keywords=["data engineer"], max_pages=1)

        assert isinstance(jobs, list)


# ===========================================================================
# NaukriGulfSource tests
# ===========================================================================


class TestNaukriGulfSource:

    def test_instantiation(self, naukrigulf_source):
        assert naukrigulf_source.source_name == "NaukriGulf"
        assert naukrigulf_source.source_type == "Scraper"

    def test_robots_allowed_is_true_on_happy_init(self, naukrigulf_source):
        assert naukrigulf_source._robots_allowed is True

    def test_transform_job_maps_all_required_fields(self, naukrigulf_source):
        result = naukrigulf_source.transform_job(RAW_JOB_NAUKRIGULF)

        assert "source_id" in result and result["source_id"]
        assert result["source_name"] == "NaukriGulf"
        assert "ingested_at" in result
        datetime.fromisoformat(result["ingested_at"])

        raw = result["raw_data"]
        assert REQUIRED_RAW_DATA_KEYS == set(raw.keys())

    def test_transform_job_copies_core_fields(self, naukrigulf_source):
        result = naukrigulf_source.transform_job(RAW_JOB_NAUKRIGULF)
        raw = result["raw_data"]
        assert raw["job_title"] == "Data Engineer"
        assert raw["company"] == "Tech Solutions LLC"
        assert raw["location"] == "Dubai"
        assert raw["remote_allowed"] is True
        assert raw["visa_sponsorship"] is False

    def test_transform_job_source_id_is_deterministic(self, naukrigulf_source):
        id1 = naukrigulf_source.transform_job(RAW_JOB_NAUKRIGULF)["source_id"]
        id2 = naukrigulf_source.transform_job(RAW_JOB_NAUKRIGULF)["source_id"]
        assert id1 == id2

    def test_validate_job_passes_valid_job(self, naukrigulf_source):
        transformed = naukrigulf_source.transform_job(RAW_JOB_NAUKRIGULF)
        assert naukrigulf_source.validate_job(transformed) is True

    def test_validate_job_fails_missing_title(self, naukrigulf_source):
        job = {
            "source_id": "ng1",
            "source_name": "NaukriGulf",
            "raw_data": {"job_title": ""},
        }
        assert naukrigulf_source.validate_job(job) is False

    def test_validate_job_fails_missing_source_id(self, naukrigulf_source):
        job = {
            "source_name": "NaukriGulf",
            "raw_data": {"job_title": "Data Analyst"},
        }
        assert naukrigulf_source.validate_job(job) is False

    def test_fetch_jobs_returns_list_of_dicts(self, naukrigulf_source):
        listing_resp = _mock_response(NAUKRIGULF_LISTING_HTML)
        detail_resp = _mock_response(NAUKRIGULF_DETAIL_HTML)

        with patch("time.sleep"), \
             patch.object(
                 naukrigulf_source._session, "get",
                 side_effect=[listing_resp, detail_resp, detail_resp],
             ):
            jobs = naukrigulf_source.fetch_jobs(keywords=["data engineer"], max_pages=1)

        assert isinstance(jobs, list)
        assert len(jobs) >= 1
        assert "job_title" in jobs[0]

    def test_robots_disallowed_returns_empty(self):
        with patch(
            "src.ingestion.sources.naukrigulf.urllib.robotparser.RobotFileParser"
        ) as mock_rfp:
            mock_rfp.return_value.can_fetch.return_value = False
            src = NaukriGulfSource()

        assert src._robots_allowed is False
        jobs = src.fetch_jobs(keywords=["data engineer"], max_pages=1)
        assert jobs == []

    def test_http_error_resilience_does_not_raise(self, naukrigulf_source):
        with patch("time.sleep"), \
             patch.object(
                 naukrigulf_source._session, "get",
                 side_effect=requests.exceptions.ConnectionError("timeout"),
             ):
            jobs = naukrigulf_source.fetch_jobs(keywords=["data engineer"], max_pages=1)

        assert isinstance(jobs, list)


# ===========================================================================
# Module-level helper function tests (pure logic — no I/O)
# ===========================================================================


class TestBaytHelpers:

    # _parse_date -------------------------------------------------------

    def test_parse_date_iso_string(self):
        assert _parse_date("2026-07-01") == "2026-07-01"

    def test_parse_date_iso_with_time(self):
        assert _parse_date("2026-07-01T12:00:00Z") == "2026-07-01"

    def test_parse_date_relative_days_ago(self):
        result = _parse_date("3 days ago")
        assert result
        assert len(result) == 10  # YYYY-MM-DD

    def test_parse_date_relative_weeks_ago(self):
        result = _parse_date("1 week ago")
        assert result

    def test_parse_date_today(self):
        result = _parse_date("Today")
        assert result == datetime.utcnow().date().isoformat()

    def test_parse_date_empty_returns_empty(self):
        assert _parse_date("") == ""

    def test_parse_date_garbage_returns_empty(self):
        assert _parse_date("not a date at all") == ""

    # _extract_uae_city -------------------------------------------------

    def test_extract_uae_city_dubai(self):
        assert _extract_uae_city("Dubai, UAE") == "Dubai"

    def test_extract_uae_city_case_insensitive(self):
        assert _extract_uae_city("Located in abu dhabi") == "Abu Dhabi"

    def test_extract_uae_city_unknown_returns_raw(self):
        result = _extract_uae_city("Silicon Valley")
        assert result == "Silicon Valley"

    def test_extract_uae_city_empty_returns_uae(self):
        assert _extract_uae_city("") == "UAE"

    # _normalise_employment_type ----------------------------------------

    def test_normalise_fulltime(self):
        assert _normalise_employment_type("full time") == "Full-time"
        assert _normalise_employment_type("Full-Time") == "Full-time"

    def test_normalise_parttime(self):
        assert _normalise_employment_type("part-time") == "Part-time"

    def test_normalise_unknown_passthrough(self):
        assert _normalise_employment_type("Flexi Hours") == "Flexi Hours"

    def test_normalise_empty_returns_empty(self):
        assert _normalise_employment_type("") == ""

    # _infer_experience_level -------------------------------------------

    def test_infer_senior_from_keyword(self):
        assert _infer_experience_level("we need a senior data engineer") == "Senior Level"

    def test_infer_entry_level_from_keyword(self):
        assert _infer_experience_level("junior developer, entry-level role") == "Entry Level"

    def test_infer_mid_level_from_years(self):
        assert _infer_experience_level("3 years of experience required") == "Mid Level"

    def test_infer_senior_from_years(self):
        assert _infer_experience_level("8 years of experience required") == "Senior Level"

    def test_infer_empty_when_no_match(self):
        assert _infer_experience_level("looking for someone awesome") == ""
