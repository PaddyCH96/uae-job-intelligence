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
        # Two similar postings from the same company with same title but slightly different descriptions.
        # Note: Processor has content-hash dedup, so we need different URLs/descriptions to get both stored.
        first = {
            "id": "dup1",
            "job_title": "Data Engineer",
            "company": "TEST_DupCo",
            "location": "Dubai",
            "description": "Build pipelines with Python and SQL. Experience with ETL workflows required.",
            "salary_range": "AED 20,000 - 30,000",
            "remote_allowed": False,
            "url": "https://example.com/a",
            "ingested_at": "2026-07-01T00:00:00",
            "source_id": "s-dup-1",
            "source_name": "MockJobBoard",
        }
        second = {
            "id": "dup2",
            "job_title": "Data Engineer",
            "company": "TEST_DupCo",
            "location": "Dubai",
            "description": "Build pipelines with Python and SQL. Experience with ETL workflows required.",
            "salary_range": "AED 20,000 - 30,000",
            "remote_allowed": False,
            "url": "https://example.com/b",
            "ingested_at": "2026-07-01T00:00:00",
            "source_id": "s-dup-2",
            "source_name": "MockJobBoard",
        }

        proc = JobProcessor()
        # Delete in FK-safe order
        db.execute(sqlalchemy.text("DELETE FROM analytics.fact_job_posting_snapshot"))
        db.execute(sqlalchemy.text("UPDATE analytics.fact_job_posting SET duplicate_of_id = NULL"))
        db.execute(sqlalchemy.text("DELETE FROM analytics.fact_job_posting"))
        db.execute(sqlalchemy.text("DELETE FROM raw_data.job_postings"))
        db.commit()

        # Store both jobs - processor may skip second due to content-hash dedup
        raws = []
        for j in (first, second):
            raws.append({
                "source_id": j["source_id"],
                "source_name": j["source_name"],
                "raw_data": j,
                "ingested_at": j["ingested_at"],
            })
        proc.store_raw_jobs(raws)
        proc.process_unprocessed_jobs(limit=10)

        # Check how many fact rows were created
        fact_count = db.execute(
            sqlalchemy.text("SELECT count(*) FROM analytics.fact_job_posting")
        ).scalar()

        if fact_count < 2:
            # Processor's content-hash dedup prevented storing both.
            # Insert the second job manually to test the dedup engine.
            # First get IDs we need
            source_id = db.execute(
                sqlalchemy.text("SELECT source_id FROM analytics.dim_source LIMIT 1")
            ).scalar()
            company_id = db.execute(
                sqlalchemy.text("SELECT company_id FROM analytics.dim_company WHERE company_name = 'TEST_DupCo'")
            ).scalar()
            location_id = db.execute(
                sqlalchemy.text("SELECT location_id FROM analytics.dim_location WHERE city = 'Dubai'")
            ).scalar()
            currency_id = db.execute(
                sqlalchemy.text("SELECT currency_id FROM analytics.dim_currency WHERE currency_code = 'AED'")
            ).scalar()
            exp_id = db.execute(
                sqlalchemy.text("SELECT experience_level_id FROM analytics.dim_experience_level WHERE level_name = 'Mid Level'")
            ).scalar()
            emp_id = db.execute(
                sqlalchemy.text("SELECT employment_type_id FROM analytics.dim_employment_type WHERE type_name = 'Full-time'")
            ).scalar()

            # Insert second job directly with a different content hash
            db.execute(sqlalchemy.text("""
                INSERT INTO analytics.fact_job_posting (
                    job_title, job_description, posted_date,
                    salary_min, salary_max, currency_id,
                    experience_level_id, employment_type_id,
                    company_id, location_id, source_id,
                    content_hash, is_active
                ) VALUES (
                    'Data Engineer',
                    'Build pipelines with Python and SQL. Experience with ETL workflows required.',
                    CURRENT_DATE,
                    20000, 30000, :currency_id,
                    :exp_id, :emp_id,
                    :company_id, :location_id, :source_id,
                    md5('Data Engineer|TEST_DupCo|Build pipelines with Python and SQL.'),
                    true
                )
            """), {
                "currency_id": currency_id,
                "exp_id": exp_id,
                "emp_id": emp_id,
                "company_id": company_id,
                "location_id": location_id,
                "source_id": source_id,
            })
            db.commit()

        # Now run deduplication - should find the duplicate
        checked, dups = DeduplicationEngine(similarity_threshold=0.85).deduplicate_jobs()
        assert dups >= 1, "Identical same-company postings should be flagged duplicate"

        active = db.execute(
            sqlalchemy.text(
                "SELECT count(*) FROM analytics.fact_job_posting "
                "WHERE is_active=TRUE AND is_duplicate=FALSE"
            )
        ).scalar()
        assert active == 1
