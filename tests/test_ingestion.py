"""Unit tests for ingestion base + MockSource (no DB required)."""

import pytest

from src.ingestion.base import BaseSource, MockSource


class TestMockSource:
    def test_fetch_count(self):
        jobs = MockSource().fetch_jobs(count=7)
        assert len(jobs) == 7

    def test_fetch_default(self):
        jobs = MockSource().fetch_jobs()
        assert len(jobs) == 10

    def test_mock_job_shape(self):
        job = MockSource().fetch_jobs(count=1)[0]
        for key in ("id", "job_title", "company", "location", "description", "salary_range", "url"):
            assert key in job

    def test_fetch_and_transform_produces_valid(self):
        jobs = MockSource().fetch_and_transform(count=5)
        assert len(jobs) == 5
        for j in jobs:
            assert j["source_name"] == "MockJobBoard"
            assert "source_id" in j and j["source_id"]
            assert "raw_data" in j and "ingested_at" in j


class TestValidation:
    def setup_method(self):
        self.src = MockSource()

    def test_valid_job_passes(self):
        job = {
            "source_id": "abc",
            "source_name": "MockJobBoard",
            "raw_data": {"job_title": "Data Engineer"},
        }
        assert self.src.validate_job(job) is True

    def test_missing_required_field_fails(self):
        job = {"source_id": "abc", "source_name": "MockJobBoard", "raw_data": {}}
        # raw_data present but no title -> should fail
        assert self.src.validate_job(job) is False

    def test_missing_source_id_fails(self):
        job = {"source_name": "MockJobBoard", "raw_data": {"title": "X"}}
        assert self.src.validate_job(job) is False

    def test_title_alias_accepted(self):
        job = {"source_id": "a", "source_name": "s", "raw_data": {"title": "Analyst"}}
        assert self.src.validate_job(job) is True


class TestTransformResilience:
    def test_transform_error_skips_job(self):
        """A source whose transform raises on one job should not abort the batch."""

        class FlakySource(BaseSource):
            def __init__(self):
                super().__init__("Flaky", "Mock")

            def fetch_jobs(self, **kwargs):
                return [{"id": 1, "title": "Good"}, {"id": 2, "title": "Bad"}]

            def transform_job(self, raw_job):
                if raw_job.get("id") == 2:
                    raise ValueError("boom")
                return {
                    "source_id": "s1",
                    "source_name": self.source_name,
                    "raw_data": raw_job,
                    "ingested_at": "2026-07-01T00:00:00",
                }

        out = FlakySource().fetch_and_transform()
        assert len(out) == 1  # bad job skipped, good job survives

    def test_fetch_error_propagates(self):
        class BrokenSource(BaseSource):
            def __init__(self):
                super().__init__("Broken", "Mock")

            def fetch_jobs(self, **kwargs):
                raise RuntimeError("network down")

        with pytest.raises(RuntimeError):
            BrokenSource().fetch_and_transform()
