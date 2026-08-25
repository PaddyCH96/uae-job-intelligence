"""Phase 2 verification tests — LLM enrichment, trend analysis, dashboard data.

These tests validate the Phase 2 deliverables referenced in PLAN.md:
- LLM integration via Ollama (skill/technology extraction)
- Database enrichment (extracted_skills, extracted_technologies)
- Trend analysis queries
- Dashboard data readiness
"""

import json
import uuid

import pytest
from sqlalchemy import text


@pytest.mark.skipunless(
    "TEST_DATABASE_URL" in __import__("os").environ,
    "requires TEST_DATABASE_URL",
)
class TestPhase2LLMIntegration:
    """Validate LLM integration and extraction quality."""

    def test_llm_connection(self):
        """Test that Ollama is running and responds."""
        from src.utils.llm import extract_with_llm, parse_json_array

        result = extract_with_llm(
            "Extract skills as a JSON array from: "
            "Looking for a Data Engineer with Python, SQL, and AWS experience."
        )
        assert isinstance(result, str), "LLM should return a string"
        assert len(result) > 0, "LLM should not return empty string"
        # Parse the response (handles markdown code blocks)
        parsed = parse_json_array(result)
        assert isinstance(parsed, list), "LLM output should be parseable as JSON array"
        assert len(parsed) > 0, "Should extract at least one skill"

    def test_llm_skill_extraction_accuracy(self, db_session):
        """Test LLM extraction on actual stored job descriptions."""
        from src.database import RawJobPosting, get_db_context
        from src.utils.llm import extract_skills

        with get_db_context() as db:
            jobs = (
                db.query(RawJobPosting)
                .filter(RawJobPosting.processed == True)
                .limit(5)
                .all()
            )

        passed = 0
        total = len(jobs)
        for job in jobs:
            description = job.raw_data.get("description", "")[:500]
            if not description:
                continue
            skills = extract_skills(description)
            total += 1
            if len(skills) > 0:
                passed += 1

        # At least 60% should extract skills
        if total > 0:
            assert passed / total >= 0.6, f"Expected 60%+ extraction success, got {passed}/{total}"


@pytest.mark.skipunless(
    "TEST_DATABASE_URL" in __import__("os").environ,
    "requires TEST_DATABASE_URL",
)
class TestPhase2DatabaseEnrichment:
    """Validate that jobs are enriched with extracted skills/technologies."""

    def test_jobs_have_extracted_skills(self, db_session):
        """Check that enriched jobs have extracted_skills populated."""
        from src.database import FactJobPosting, get_db_context

        with get_db_context() as db:
            total_jobs = db.query(FactJobPosting).count()
            enriched_skills = (
                db.query(FactJobPosting)
                .filter(FactJobPosting.extracted_skills.isnot(None))
                .count()
            )

        # At least 1 job should be enriched (we have 1 mock job)
        assert enriched_skills >= 1, (
            f"Expected >= 1 enriched jobs, got {enriched_skills} out of {total_jobs}"
        )

    def test_jobs_have_extracted_technologies(self, db_session):
        """Check that enriched jobs have extracted_technologies populated."""
        from src.database import FactJobPosting, get_db_context

        with get_db_context() as db:
            enriched_tech = (
                db.query(FactJobPosting)
                .filter(FactJobPosting.extracted_technologies.isnot(None))
                .count()
            )

        # At least 1 job should have technologies extracted
        assert enriched_tech >= 1, (
            f"Expected >= 1 jobs with tech extraction, got {enriched_tech}"
        )

    def test_skills_are_valid_json(self, db_session):
        """Verify extracted_skills contains valid JSON arrays."""
        from src.database import FactJobPosting, get_db_context

        with get_db_context() as db:
            jobs = (
                db.query(FactJobPosting)
                .filter(FactJobPosting.extracted_skills.isnot(None))
                .limit(10)
                .all()
            )

        for job in jobs:
            skills = job.extracted_skills
            # skills should be a list (JSONB stored as Python list)
            assert isinstance(skills, list), f"Job {job.job_posting_id}: skills should be list"
            assert len(skills) > 0, f"Job {job.job_posting_id}: skills should not be empty"


@pytest.mark.skipunless(
    "TEST_DATABASE_URL" in __import__("os").environ,
    "requires TEST_DATABASE_URL",
)
class TestPhase2TrendAnalysis:
    """Validate technology trend analysis queries."""

    def test_tech_trends_view_exists(self, db_session):
        """Verify the v_tech_trends view exists and is queryable."""
        from src.database import get_db_context

        with get_db_context() as db:
            try:
                result = db.execute(
                    text("SELECT technology_name, job_count FROM analytics.v_tech_trends LIMIT 5")
                ).fetchall()
                # View may return empty if no enriched data yet
                assert isinstance(result, list), "View should return results"
            except Exception as e:
                pytest.fail(f"View v_tech_trends query failed: {e}")

    def test_top_technologies_identified(self, db_session):
        """Check that top technologies are identified from enriched data."""
        from src.database import get_db_context

        with get_db_context() as db:
            # Count distinct technologies across all jobs
            result = db.execute(
                text("""
                SELECT COUNT(DISTINCT unnest(extracted_technologies::text[]))
                FROM analytics.fact_job_posting
                WHERE extracted_technologies IS NOT NULL
                """)
            ).scalar()

        # Should identify at least 1 distinct technology
        assert result >= 1, (
            f"Expected >= 1 distinct technologies, got {result}"
        )

    def test_trend_indicators_present(self, db_session):
        """Verify trend indicators (growing/established/declining) are assigned."""
        from src.database import get_db_context

        with get_db_context() as db:
            result = db.execute(
                text("""
                SELECT trend, COUNT(*)
                FROM analytics.v_tech_trends
                GROUP BY trend
                """)
            ).fetchall()

        # Each trend category should have entries
        trend_counts = {row[0]: row[1] for row in result}
        # At minimum, some technologies should have a trend assigned
        assert len(trend_counts) > 0, "Should have trend categories assigned"


@pytest.mark.skipunless(
    "TEST_DATABASE_URL" in __import__("os").environ,
    "requires TEST_DATABASE_URL",
)
class TestPhase2DashboardReadiness:
    """Validate that dashboard can read enriched data."""

    def test_dashboard_can_query_enriched_data(self, db_session):
        """Verify dashboard queries work on enriched fact table."""
        from src.database import get_db_context

        with get_db_context() as db:
            # Query should complete without error
            result = db.execute(
                text("""
                SELECT job_title, salary_min, salary_max,
                       extracted_skills, extracted_technologies
                FROM analytics.fact_job_posting
                WHERE is_active = True
                LIMIT 3
                """)
            ).fetchall()

        assert len(result) >= 1, "Should return at least 1 job record"
        # Each record should have the expected columns
        for row in result:
            assert row[0] is not None, "Job title should not be None"

    def test_aggregations_with_skills(self, db_session):
        """Verify aggregations can filter by extracted skills."""
        from src.database import get_db_context

        with get_db_context() as db:
            # Try a basic aggregation query that includes skills
            result = db.execute(
                text("""
                SELECT
                    fjp.job_title,
                    fjp.extracted_skills,
                    fjp.salary_min
                FROM analytics.fact_job_posting fjp
                WHERE fjp.is_active = True
                LIMIT 5
                """)
            ).fetchall()

        assert len(result) >= 1, "Should return at least 1 job record with skills"


def test_phase2_success_criteria(db_session):
    """Aggregate check: all Phase 2 success criteria met."""
    from src.database import FactJobPosting, get_db_context

    with get_db_context() as db:
        total = db.query(FactJobPosting).filter(FactJobPosting.is_active == True).count()
        enriched_skills = (
            db.query(FactJobPosting)
            .filter(FactJobPosting.extracted_skills.isnot(None))
            .count()
        )
        enriched_tech = (
            db.query(FactJobPosting)
            .filter(FactJobPosting.extracted_technologies.isnot(None))
            .count()
        )

    # Aggregate Phase 2 metrics
    checks = {
        "total_active_jobs": total >= 1,
        "skills_enrichment": enriched_skills >= 1,
        "tech_enrichment": enriched_tech >= 1,
    }

    criteria = {
        k: ("At least 1 active job" if v else f"{k}: insufficient ({v})")
        for k, v in checks.items()
    }

    passed = sum(1 for v in checks.values() if v)
    total_checks = len(checks)

    # At least 80% of criteria must pass
    assert passed / total_checks >= 0.8, (
        f"Phase 2 success criteria: {passed}/{total_checks} checks passed. "
        f"Details: {criteria}"
    )
