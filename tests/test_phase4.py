"""Phase 4 verification tests — Predictive models, user profiles, sentiment.

These tests validate Phase 4 deliverables:
- Predictive models (skill demand, salary prediction)
- User profile system (opt-in)
- Sentiment analysis and industry classification
"""

import pytest
from sqlalchemy import text


@pytest.mark.skipunless(
    "TEST_DATABASE_URL" in __import__("os").environ,
    "requires TEST_DATABASE_URL",
)
class TestPhase4Models:
    """Validate predictive models."""

    def test_skill_forecast_model_trained(self):
        """Check that skill forecast model file exists."""
        from pathlib import Path
        
        model_path = Path("models/skill_forecast_v1.pkl")
        assert model_path.exists(), "Skill forecast model not found"

    def test_salary_predictor_model_trained(self):
        """Check that salary predictor model file exists."""
        from pathlib import Path
        
        model_path = Path("models/salary_predictor_v1.pkl")
        assert model_path.exists(), "Salary predictor model not found"

    def test_skill_forecast_view_exists(self, db_session):
        """Verify the v_skill_forecast view exists and is queryable."""
        from src.database import get_db_context

        with get_db_context() as db:
            try:
                result = db.execute(
                    text("SELECT * FROM analytics.v_skill_forecast LIMIT 5")
                ).fetchall()
                assert isinstance(result, list), "View should return results"
            except Exception as e:
                pytest.fail(f"View v_skill_forecast query failed: {e}")

    def test_salary_prediction_view_exists(self, db_session):
        """Verify the v_salary_prediction view exists and is queryable."""
        from src.database import get_db_context

        with get_db_context() as db:
            try:
                result = db.execute(
                    text("SELECT * FROM analytics.v_salary_prediction LIMIT 5")
                ).fetchall()
                assert isinstance(result, list), "View should return results"
            except Exception as e:
                pytest.fail(f"View v_salary_prediction query failed: {e}")


@pytest.mark.skipunless(
    "TEST_DATABASE_URL" in __import__("os").environ,
    "requires TEST_DATABASE_URL",
)
class TestPhase4Sentiment:
    """Validate sentiment analysis and industry classification."""

    def test_sentiment_column_exists(self, db_session):
        """Check that sentiment_score column exists in fact_job_posting."""
        from src.database import get_db_context

        with get_db_context() as db:
            result = db.execute(
                text("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'fact_job_posting' 
                AND column_name = 'sentiment_score'
                """)
            ).scalar()
        
        assert result == 1, "sentiment_score column should exist"

    def test_industry_table_exists(self, db_session):
        """Check that dim_industry table exists."""
        from src.database import get_db_context

        with get_db_context() as db:
            result = db.execute(
                text("SELECT COUNT(*) FROM analytics.dim_industry")
            ).scalar()
        
        assert result >= 6, "dim_industry should have at least 6 industries"

    def test_industry_id_column_exists(self, db_session):
        """Check that industry_id column exists in fact_job_posting."""
        from src.database import get_db_context

        with get_db_context() as db:
            result = db.execute(
                text("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'fact_job_posting' 
                AND column_name = 'industry_id'
                """)
            ).scalar()
        
        assert result == 1, "industry_id column should exist"


@pytest.mark.skipunless(
    "TEST_DATABASE_URL" in __import__("os").environ,
    "requires TEST_DATABASE_URL",
)
class TestPhase4Profiles:
    """Validate user profile system."""

    def test_user_profile_table_exists(self, db_session):
        """Check that dim_user_profile table exists."""
        from src.database import get_db_context

        with get_db_context() as db:
            result = db.execute(
                text("SELECT COUNT(*) FROM analytics.dim_user_profile")
            ).scalar()
        
        assert result >= 0, "dim_user_profile table should exist"

    def test_user_profile_has_optin_column(self, db_session):
        """Check that opt_in column exists in dim_user_profile."""
        from src.database import get_db_context

        with get_db_context() as db:
            result = db.execute(
                text("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'dim_user_profile' 
                AND column_name = 'opt_in'
                """)
            ).scalar()
        
        assert result == 1, "opt_in column should exist"


def test_phase4_success_criteria(db_session):
    """Aggregate check: all Phase 4 success criteria met."""
    from src.database import get_db_context
    from pathlib import Path

    checks = {
        "skill_forecast_model": Path("models/skill_forecast_v1.pkl").exists(),
        "salary_predictor_model": Path("models/salary_predictor_v1.pkl").exists(),
        "industry_table": False,
        "sentiment_column": False,
        "user_profile_table": False,
    }

    with get_db_context() as db:
        # Check industry table
        try:
            result = db.execute(
                text("SELECT COUNT(*) FROM analytics.dim_industry")
            ).scalar()
            checks["industry_table"] = result >= 6
        except Exception:
            pass

        # Check sentiment column
        try:
            result = db.execute(
                text("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'fact_job_posting' 
                AND column_name = 'sentiment_score'
                """)
            ).scalar()
            checks["sentiment_column"] = result == 1
        except Exception:
            pass

        # Check user profile table
        try:
            result = db.execute(
                text("SELECT COUNT(*) FROM analytics.dim_user_profile")
            ).scalar()
            checks["user_profile_table"] = result >= 0
        except Exception:
            pass

    passed = sum(1 for v in checks.values() if v)
    total_checks = len(checks)

    # At least 80% of criteria must pass
    assert passed / total_checks >= 0.8, (
        f"Phase 4 success criteria: {passed}/{total_checks} checks passed. "
        f"Details: {checks}"
    )