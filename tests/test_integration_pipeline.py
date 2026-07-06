"""Integration tests for the ingestion -> normalize -> dedup pipeline (DB required).

These exercise the real JobProcessor and DeduplicationEngine against the test
database. They also encode two suspected Phase-1 defects so the report can cite
executed evidence rather than static reasoning.
"""

import sqlalchemy


class TestNormalization:
    def test_raw_then_normalize_creates_fact(self, clean_facts):
        from src.ingestion.base import MockSource
        from src.ingestion.processor import JobProcessor

        db = clean_facts
        jobs = MockSource().fetch_and_transform(count=3)
        proc = JobProcessor()
        stored = proc.store_raw_jobs(jobs)
        assert stored == 3

        processed = proc.process_unprocessed_jobs(limit=10)
        assert processed == 3

        fact_count = db.execute(
            sqlalchemy.text("SELECT count(*) FROM analytics.fact_job_posting")
        ).scalar()
        assert fact_count == 3

    def test_salary_normalized_into_columns(self, clean_facts):
        from src.ingestion.base import MockSource
        from src.ingestion.processor import JobProcessor

        db = clean_facts
        jobs = MockSource().fetch_and_transform(count=1)
        proc = JobProcessor()
        proc.store_raw_jobs(jobs)
        proc.process_unprocessed_jobs(limit=1)

        row = db.execute(
            sqlalchemy.text(
                "SELECT salary_min, salary_max FROM analytics.fact_job_posting LIMIT 1"
            )
        ).first()
        # Mock salary is 'AED 15,000 - 25,000' -> should parse.
        assert row.salary_min == 15000 and row.salary_max == 25000


class TestReprocessingIdempotency:
    def test_reingest_does_not_double_process_raw(self, clean_facts):
        """
        BUG PROBE: process_unprocessed_jobs marks raw_job.processed=True on a
        *different* session than the one that loaded it. If the flag doesn't
        persist, a second processing pass will re-create fact rows.
        """
        from src.ingestion.base import MockSource
        from src.ingestion.processor import JobProcessor

        db = clean_facts
        jobs = MockSource().fetch_and_transform(count=2)
        proc = JobProcessor()
        proc.store_raw_jobs(jobs)

        proc.process_unprocessed_jobs(limit=10)
        first = db.execute(
            sqlalchemy.text("SELECT count(*) FROM analytics.fact_job_posting")
        ).scalar()

        # Run the processing pass again. If 'processed' persisted, no new facts.
        proc.process_unprocessed_jobs(limit=10)
        second = db.execute(
            sqlalchemy.text("SELECT count(*) FROM analytics.fact_job_posting")
        ).scalar()

        assert second == first, (
            f"Reprocessing created duplicate facts: {first} -> {second}. "
            "raw_job.processed flag likely not persisted."
        )


class TestDeduplicationPersistence:
    def test_identical_jobs_are_deduplicated(self, clean_facts):
        from src.ingestion.processor import JobProcessor
        from src.deduplication.engine import DeduplicationEngine

        db = clean_facts
        # Two identical postings from the same source/company.
        identical = {
            "id": "dup1",
            "job_title": "Data Engineer",
            "company": "TEST_DupCo",
            "location": "Dubai",
            "description": "Build pipelines with Python and SQL.",
            "salary_range": "AED 20,000 - 30,000",
            "remote_allowed": False,
            "url": "https://example.com/a",
            "ingested_at": "2026-07-01T00:00:00",
            "source_id": "s-dup-1",
            "source_name": "MockJobBoard",
        }
        second = dict(identical, id="dup2", source_id="s-dup-2", url="https://example.com/b")

        proc = JobProcessor()
        proc.store_raw_jobs([
            {k: identical[k] for k in ("source_id", "source_name", "raw_data", "ingested_at")}
            if False else identical,  # keep raw dict shape from transform
        ])
        # store_raw_jobs expects transform output shape; build it explicitly:
        raws = []
        for j in (identical, second):
            raws.append(
                {
                    "source_id": j["source_id"],
                    "source_name": j["source_name"],
                    "raw_data": j,
                    "ingested_at": j["ingested_at"],
                }
            )
        # reset and store cleanly
        db.execute(sqlalchemy.text("DELETE FROM raw_data.job_postings"))
        db.commit()
        proc.store_raw_jobs(raws)
        proc.process_unprocessed_jobs(limit=10)

        checked, dups = DeduplicationEngine(similarity_threshold=0.85).deduplicate_jobs()
        assert dups >= 1, "Identical same-company postings should be flagged duplicate"

        active = db.execute(
            sqlalchemy.text(
                "SELECT count(*) FROM analytics.fact_job_posting "
                "WHERE is_active=TRUE AND is_duplicate=FALSE"
            )
        ).scalar()
        assert active == 1
