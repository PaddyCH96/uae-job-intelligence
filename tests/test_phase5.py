"""Phase 5 verification tests — Stretch Goals (Experimental).

These tests validate Phase 5 deliverables:
- Real-time monitoring
- Multi-language support
- Geospatial insights
- Community features
- MLOps baseline
"""

import pytest
from sqlalchemy import text


@pytest.mark.skipunless(
    "TEST_DATABASE_URL" in __import__("os").environ,
    "requires TEST_DATABASE_URL",
)
class TestPhase5MultiLanguage:
    """Validate multi-language support."""

    def test_language_column_exists(self, db_session):
        """Check that language column exists in job_postings."""
        from src.database import get_db_context

        with get_db_context() as db:
            result = db.execute(
                text("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'job_postings' 
                AND column_name = 'language'
                """)
            ).scalar()
        
        assert result == 1, "language column should exist"

    def test_language_detection(self):
        """Test language detection on sample text."""
        from src.utils.multilang import detect_language
        
        # English text
        lang, conf = detect_language("Looking for a Python developer with SQL experience")
        assert lang == 'en', f"Expected 'en', got '{lang}'"
        
        # Arabic text
        lang, conf = detect_language("نبحث عن مطور بايثون ذو خبرة في SQL")
        assert lang == 'ar', f"Expected 'ar', got '{lang}'"
        
        # Mixed text
        lang, conf = detect_language("Looking for Python developer with خبرة in ML")
        assert lang in ['ar', 'mixed'], f"Expected 'ar' or 'mixed', got '{lang}'"


@pytest.mark.skipunless(
    "TEST_DATABASE_URL" in __import__("os").environ,
    "requires TEST_DATABASE_URL",
)
class TestPhase5Geospatial:
    """Validate geospatial insights."""

    def test_district_table_exists(self, db_session):
        """Check that dim_district table exists."""
        from src.database import get_db_context

        with get_db_context() as db:
            result = db.execute(
                text("SELECT COUNT(*) FROM analytics.dim_district")
            ).scalar()
        
        assert result >= 10, "dim_district should have at least 10 districts"

    def test_geo_distribution_view_exists(self, db_session):
        """Check that v_geo_distribution view exists."""
        from src.database import get_db_context

        with get_db_context() as db:
            try:
                result = db.execute(
                    text("SELECT * FROM analytics.v_geo_distribution LIMIT 5")
                ).fetchall()
                assert isinstance(result, list), "View should return results"
            except Exception as e:
                pytest.fail(f"View v_geo_distribution query failed: {e}")

    def test_extract_district(self):
        """Test district extraction from location string."""
        from src.utils.geospatial import extract_district_from_location
        
        district = extract_district_from_location("Dubai Marina, Dubai, UAE")
        assert district == "Dubai Marina", f"Expected 'Dubai Marina', got '{district}'"
        
        district = extract_district_from_location("Abu Dhabi, UAE")
        assert district == "Abu Dhabi", f"Expected 'Abu Dhabi', got '{district}'"


@pytest.mark.skipunless(
    "TEST_DATABASE_URL" in __import__("os").environ,
    "requires TEST_DATABASE_URL",
)
class TestPhase5Community:
    """Validate community features."""

    def test_insights_table_exists(self, db_session):
        """Check that user_shared_insights table exists."""
        from src.database import get_db_context

        with get_db_context() as db:
            result = db.execute(
                text("SELECT COUNT(*) FROM analytics.user_shared_insights")
            ).scalar()
        
        assert result >= 0, "user_shared_insights table should exist"

    def test_saved_searches_table_exists(self, db_session):
        """Check that user_saved_searches table exists."""
        from src.database import get_db_context

        with get_db_context() as db:
            result = db.execute(
                text("SELECT COUNT(*) FROM analytics.user_saved_searches")
            ).scalar()
        
        assert result >= 0, "user_saved_searches table should exist"


@pytest.mark.skipunless(
    "TEST_DATABASE_URL" in __import__("os").environ,
    "requires TEST_DATABASE_URL",
)
class TestPhase5MLOps:
    """Validate MLOps baseline."""

    def test_metadata_file_exists(self):
        """Check that model metadata file exists."""
        from pathlib import Path
        
        metadata_path = Path("models/metadata.json")
        assert metadata_path.exists(), "Model metadata file should exist"

    def test_models_directory_exists(self):
        """Check that models directory exists."""
        from pathlib import Path
        
        models_dir = Path("models")
        assert models_dir.exists(), "Models directory should exist"
        assert models_dir.is_dir(), "Models should be a directory"


def test_phase5_success_criteria(db_session):
    """Aggregate check: Phase 5 success criteria met."""
    from src.database import get_db_context
    from pathlib import Path

    checks = {
        "language_column": False,
        "district_table": False,
        "geo_view": False,
        "insights_table": False,
        "searches_table": False,
        "metadata_file": Path("models/metadata.json").exists(),
    }

    with get_db_context() as db:
        # Check language column
        try:
            result = db.execute(
                text("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'job_postings' 
                AND column_name = 'language'
                """)
            ).scalar()
            checks["language_column"] = result == 1
        except Exception:
            pass

        # Check district table
        try:
            result = db.execute(
                text("SELECT COUNT(*) FROM analytics.dim_district")
            ).scalar()
            checks["district_table"] = result >= 10
        except Exception:
            pass

        # Check geo view
        try:
            result = db.execute(
                text("SELECT COUNT(*) FROM analytics.v_geo_distribution")
            ).scalar()
            checks["geo_view"] = result >= 0
        except Exception:
            pass

        # Check insights table
        try:
            result = db.execute(
                text("SELECT COUNT(*) FROM analytics.user_shared_insights")
            ).scalar()
            checks["insights_table"] = result >= 0
        except Exception:
            pass

        # Check searches table
        try:
            result = db.execute(
                text("SELECT COUNT(*) FROM analytics.user_saved_searches")
            ).scalar()
            checks["searches_table"] = result >= 0
        except Exception:
            pass

    passed = sum(1 for v in checks.values() if v)
    total_checks = len(checks)

    # At least 80% of criteria must pass
    assert passed / total_checks >= 0.8, (
        f"Phase 5 success criteria: {passed}/{total_checks} checks passed. "
        f"Details: {checks}"
    )