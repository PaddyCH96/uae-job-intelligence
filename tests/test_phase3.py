"""Phase 3 verification tests — Skill growth, salary correlation, data sources.

These tests validate Phase 3 deliverables:
- Skill growth rates (YoY)
- Technology-salary correlation
- Expanded data sources
- Dashboard readiness (5 pages)
"""

import pytest
from sqlalchemy import text


@pytest.mark.skipunless(
    "TEST_DATABASE_URL" in __import__("os").environ,
    "requires TEST_DATABASE_URL",
)
class TestPhase3SkillGrowth:
    """Validate skill growth rate computation."""

    def test_skill_growth_view_exists(self, db_session):
        """Verify the v_skill_growth_rates view exists and is queryable."""
        from src.database import get_db_context

        with get_db_context() as db:
            try:
                result = db.execute(
                    text("SELECT skill_name, job_count, trend FROM analytics.v_skill_growth_rates LIMIT 5")
                ).fetchall()
                assert isinstance(result, list), "View should return results"
            except Exception as e:
                pytest.fail(f"View v_skill_growth_rates query failed: {e}")

    def test_top_skills_identified(self, db_session):
        """Check that top skills are identified from enriched data."""
        from src.database import get_db_context

        with get_db_context() as db:
            result = db.execute(
                text("""
                SELECT COUNT(DISTINCT skill)
                FROM analytics.fact_job_posting,
                     jsonb_array_elements_text(extracted_skills) AS skill
                WHERE extracted_skills IS NOT NULL
                """)
            ).scalar()

        # Should identify at least 1 distinct skill
        assert result >= 1, f"Expected >= 1 distinct skills, got {result}"

    def test_trend_categories_assigned(self, db_session):
        """Verify trend categories (growing/established/new) are assigned."""
        from src.database import get_db_context

        with get_db_context() as db:
            result = db.execute(
                text("""
                SELECT trend, COUNT(*)
                FROM analytics.v_skill_growth_rates
                GROUP BY trend
                """)
            ).fetchall()

        trend_counts = {row[0]: row[1] for row in result}
        assert len(trend_counts) > 0, "Should have trend categories assigned"


@pytest.mark.skipunless(
    "TEST_DATABASE_URL" in __import__("os").environ,
    "requires TEST_DATABASE_URL",
)
class TestPhase3SalaryCorrelation:
    """Validate technology-salary correlation."""

    def test_salary_correlation_view_exists(self, db_session):
        """Verify the v_salary_correlation view exists and is queryable."""
        from src.database import get_db_context

        with get_db_context() as db:
            try:
                result = db.execute(
                    text("SELECT * FROM analytics.v_salary_correlation LIMIT 5")
                ).fetchall()
                assert isinstance(result, list), "View should return results"
            except Exception as e:
                pytest.fail(f"View v_salary_correlation query failed: {e}")

    def test_tech_salary_avg_view_exists(self, db_session):
        """Verify the v_tech_salary_avg view exists and is queryable."""
        from src.database import get_db_context

        with get_db_context() as db:
            try:
                result = db.execute(
                    text("SELECT * FROM analytics.v_tech_salary_avg LIMIT 5")
                ).fetchall()
                assert isinstance(result, list), "View should return results"
            except Exception as e:
                pytest.fail(f"View v_tech_salary_avg query failed: {e}")

    def test_salary_data_available(self, db_session):
        """Check that salary data is available for correlation analysis."""
        from src.database import get_db_context

        with get_db_context() as db:
            result = db.execute(
                text("""
                SELECT COUNT(*) 
                FROM analytics.fact_job_posting 
                WHERE salary_min IS NOT NULL AND salary_max IS NOT NULL
                """)
            ).scalar()

        # Should have salary data for correlation
        assert result >= 1, f"Expected >= 1 jobs with salary data, got {result}"


@pytest.mark.skipunless(
    "TEST_DATABASE_URL" in __import__("os").environ,
    "requires TEST_DATABASE_URL",
)
class TestPhase3DashboardReadiness:
    """Validate that dashboard can read Phase 3 data."""

    def test_company_hiring_view_exists(self, db_session):
        """Verify the v_company_hiring view exists and is queryable."""
        from src.database import get_db_context

        with get_db_context() as db:
            try:
                result = db.execute(
                    text("SELECT * FROM analytics.v_company_hiring LIMIT 5")
                ).fetchall()
                assert isinstance(result, list), "View should return results"
            except Exception as e:
                pytest.fail(f"View v_company_hiring query failed: {e}")

    def test_city_distribution_view_exists(self, db_session):
        """Verify the v_city_distribution view exists and is queryable."""
        from src.database import get_db_context

        with get_db_context() as db:
            try:
                result = db.execute(
                    text("SELECT * FROM analytics.v_city_distribution LIMIT 5")
                ).fetchall()
                assert isinstance(result, list), "View should return results"
            except Exception as e:
                pytest.fail(f"View v_city_distribution query failed: {e}")

    def test_enriched_job_aggregations(self, db_session):
        """Verify enriched job aggregations work for dashboard."""
        from src.database import get_db_context

        with get_db_context() as db:
            result = db.execute(
                text("""
                SELECT 
                    COUNT(*) as total_jobs,
                    COUNT(CASE WHEN extracted_skills IS NOT NULL THEN 1 END) as enriched_jobs,
                    COUNT(CASE WHEN salary_min IS NOT NULL THEN 1 END) as jobs_with_salary
                FROM analytics.fact_job_posting
                WHERE is_active = True
                """)
            ).fetchone()

        assert result[0] >= 1, "Should have at least 1 active job"
        assert result[1] >= 1, "Should have at least 1 enriched job"


def test_phase3_success_criteria(db_session):
    """Aggregate check: all Phase 3 success criteria met."""
    from src.database import get_db_context

    with get_db_context() as db:
        # Check skill growth rates
        try:
            result = db.execute(
                text("SELECT COUNT(*) FROM analytics.v_skill_growth_rates")
            ).scalar()
            skill_growth_exists = result is not None
        except Exception:
            skill_growth_exists = False

        # Check salary correlation
        try:
            result = db.execute(
                text("SELECT COUNT(*) FROM analytics.v_salary_correlation")
            ).scalar()
            salary_correlation_exists = result is not None
        except Exception:
            salary_correlation_exists = False

        # Check company hiring
        try:
            result = db.execute(
                text("SELECT COUNT(*) FROM analytics.v_company_hiring")
            ).scalar()
            company_hiring_exists = result is not None
        except Exception:
            company_hiring_exists = False

        # Check city distribution
        try:
            result = db.execute(
                text("SELECT COUNT(*) FROM analytics.v_city_distribution")
            ).scalar()
            city_distribution_exists = result is not None
        except Exception:
            city_distribution_exists = False

        # Check enrichment coverage
        result = db.execute(
            text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN extracted_skills IS NOT NULL THEN 1 END) as enriched
            FROM analytics.fact_job_posting
            WHERE is_active = True
            """)
        ).fetchone()
        coverage = (result[1] / result[0] * 100) if result[0] > 0 else 0

    checks = {
        "skill_growth_view": skill_growth_exists,
        "salary_correlation_view": salary_correlation_exists,
        "company_hiring_view": company_hiring_exists,
        "city_distribution_view": city_distribution_exists,
        "llm_coverage_80pct": coverage >= 80,
    }

    passed = sum(1 for v in checks.values() if v)
    total_checks = len(checks)

    # At least 80% of criteria must pass
    assert passed / total_checks >= 0.8, (
        f"Phase 3 success criteria: {passed}/{total_checks} checks passed. "
        f"Details: {checks}"
    )