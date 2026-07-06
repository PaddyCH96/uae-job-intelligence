"""API endpoint tests using FastAPI TestClient (DB required).

Seeds a couple of fact rows via the processor, then asserts endpoint contracts:
health, listing, filtering, pagination, single-get 404s, search route
reachability, aggregations, and stats.
"""

import uuid

import pytest
import sqlalchemy


@pytest.fixture
def client(requires_db):
    from fastapi.testclient import TestClient
    from src.api.main import app

    return TestClient(app)


@pytest.fixture
def seeded(clean_facts):
    """Insert 2 active jobs directly for deterministic API assertions."""
    from src.ingestion.base import MockSource
    from src.ingestion.processor import JobProcessor

    jobs = MockSource().fetch_and_transform(count=2)
    proc = JobProcessor()
    proc.store_raw_jobs(jobs)
    proc.process_unprocessed_jobs(limit=10)
    return clean_facts


class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"


class TestJobsList:
    def test_list_returns_jobs(self, client, seeded):
        r = client.get("/jobs")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 1

    def test_pagination_limit(self, client, seeded):
        r = client.get("/jobs", params={"limit": 1})
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_limit_validation_rejects_over_max(self, client):
        r = client.get("/jobs", params={"limit": 5000})
        assert r.status_code == 422  # exceeds le=1000

    def test_city_filter(self, client, seeded):
        r = client.get("/jobs", params={"city": "Dubai"})
        assert r.status_code == 200
        for job in r.json():
            assert "job_title" in job

    def test_joined_fields_populated(self, client, seeded):
        """company_name and city must be non-None strings in every response row."""
        r = client.get("/jobs")
        assert r.status_code == 200
        jobs = r.json()
        assert len(jobs) >= 1
        for job in jobs:
            assert isinstance(job.get("company_name"), str), "company_name should be a string"
            assert isinstance(job.get("city"), str), "city should be a string"


class TestSingleJob:
    def test_missing_job_404(self, client, seeded):
        r = client.get(f"/jobs/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_bad_uuid_returns_error(self, client, seeded):
        # Non-UUID id: DB cast error surfaces. Documents current handling.
        r = client.get("/jobs/not-a-uuid")
        assert r.status_code in (404, 422, 500)


class TestSearchRouteReachability:
    def test_search_route_is_shadowed_bug(self, client, seeded):
        """
        BUG PROBE: /jobs/search is declared AFTER /jobs/{job_id}, so FastAPI
        matches 'search' as a job_id path param first. Expected (correct) is a
        200 list; current behavior is 404 'Job not found'. Marked xfail so the
        suite records the defect without failing the run.
        """
        r = client.get("/jobs/search", params={"q": "engineer"})
        if r.status_code == 404 and r.json().get("detail") == "Job not found":
            pytest.xfail("Confirmed: /jobs/search shadowed by /jobs/{job_id}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestAggregations:
    def test_by_company(self, client, seeded):
        r = client.get("/aggregations/by-company")
        assert r.status_code == 200
        assert all({"name", "count"} <= set(row) for row in r.json())

    def test_by_city(self, client, seeded):
        r = client.get("/aggregations/by-city")
        assert r.status_code == 200


class TestStats:
    def test_stats_shape(self, client, seeded):
        r = client.get("/stats")
        assert r.status_code == 200
        body = r.json()
        for key in (
            "total_jobs",
            "active_jobs",
            "duplicate_jobs",
            "total_companies",
            "deduplication_rate",
        ):
            assert key in body
