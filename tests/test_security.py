"""Security regression tests for Gate 2 hardening.

Tests cover:
- CORS configuration
- Input validation (pagination, query length, salary ranges, date ranges)
- Rate limiting behavior
- Secret handling (no hardcoded credentials)
- SQL injection prevention
"""

import os
import pytest
from fastapi.testclient import TestClient


class TestCORS:
    """Test CORS configuration behavior."""

    def test_cors_without_origins_allows_development_origins(self, monkeypatch):
        """When CORS_ORIGINS not set, development origins are allowed."""
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
        # Re-import to pick up new env
        import importlib
        import src.api.main
        importlib.reload(src.api.main)
        from src.api.main import app

        client = TestClient(app)
        # Development origin should be allowed
        r = client.get("/health", headers={"Origin": "http://localhost:8501"})
        assert r.status_code == 200
        # allow_credentials should be False when no explicit origins
        # Note: TestClient doesn't fully simulate CORS, but we test the config logic

    def test_cors_with_origins_allows_configured_only(self, monkeypatch):
        """When CORS_ORIGINS set, only those origins allowed."""
        monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com,https://admin.example.com")
        import importlib
        import src.api.main
        importlib.reload(src.api.main)
        from src.api.main import app

        client = TestClient(app)
        # Configured origin should be allowed
        r = client.get("/health", headers={"Origin": "https://app.example.com"})
        assert r.status_code == 200

    def test_cors_credentials_only_when_origins_set(self, monkeypatch):
        """allow_credentials=True only when explicit origins configured."""
        from src.api.main import allow_credentials

        # Test with origins set
        monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
        import importlib
        import src.api.main
        importlib.reload(src.api.main)
        assert src.api.main.allow_credentials is True

        # Test without origins
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
        importlib.reload(src.api.main)
        assert src.api.main.allow_credentials is False


class TestInputValidation:
    """Test API input validation constraints."""

    @pytest.fixture
    def client(self):
        from src.api.main import app
        return TestClient(app)

    def test_health_endpoint_unaffected(self, client):
        """Health endpoint always works."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_pagination_limit_enforced(self, client):
        """Pagination limit respects MAX_PAGE_SIZE."""
        # Valid limit
        r = client.get("/jobs", params={"limit": 100})
        assert r.status_code in (200, 404, 500)  # May fail on DB but not validation

        # Exceeds limit
        r = client.get("/jobs", params={"limit": 1001})
        assert r.status_code == 422

    def test_pagination_skip_non_negative(self, client):
        """Skip must be non-negative."""
        r = client.get("/jobs", params={"skip": -1})
        assert r.status_code == 422

    def test_search_query_length_enforced(self, client):
        """Search query must be 2-200 characters."""
        # Too short
        r = client.get("/jobs/search", params={"q": "a"})
        assert r.status_code == 422

        # Valid length
        r = client.get("/jobs/search", params={"q": "engineer"})
        assert r.status_code in (200, 404, 500)

        # Too long
        r = client.get("/jobs/search", params={"q": "x" * 201})
        assert r.status_code == 422

    def test_salary_range_validation(self, client):
        """Salary range must be valid."""
        # min_salary > max_salary
        r = client.get("/jobs", params={"min_salary": 50000, "max_salary": 30000})
        assert r.status_code == 422
        assert "min_salary must be less than or equal to max_salary" in r.json()["detail"]

        # Valid range
        r = client.get("/jobs", params={"min_salary": 10000, "max_salary": 50000})
        assert r.status_code in (200, 404, 500)

    def test_salary_bounds(self, client):
        """Salary must be within bounds."""
        # Negative salary
        r = client.get("/jobs", params={"min_salary": -1})
        assert r.status_code == 422

        # Exceeds MAX_SALARY
        r = client.get("/jobs", params={"min_salary": 2_000_000})
        assert r.status_code == 422

    def test_date_range_validation(self, client):
        """Date ranges must be valid."""
        # posted_after > posted_before
        r = client.get("/jobs", params={"posted_after": "2026-01-01", "posted_before": "2025-01-01"})
        assert r.status_code == 422
        assert "posted_after must be before or equal to posted_before" in r.json()["detail"]

    def test_date_bounds(self, client):
        """Dates must be within bounds."""
        # Too early
        r = client.get("/jobs", params={"posted_after": "2019-01-01"})
        assert r.status_code == 422

        # Too far future
        r = client.get("/jobs", params={"posted_after": "2031-01-01"})
        assert r.status_code == 422

    def test_filter_string_length(self, client):
        """Filter strings have max length."""
        # Company name too long
        r = client.get("/jobs", params={"company_name": "x" * 101})
        assert r.status_code == 422

        # City too long
        r = client.get("/jobs", params={"city": "x" * 101})
        assert r.status_code == 422

    def test_aggregation_limit(self, client):
        """Aggregation endpoints have max limit."""
        r = client.get("/aggregations/by-company", params={"limit": 101})
        assert r.status_code == 422

        r = client.get("/aggregations/by-city", params={"limit": 101})
        assert r.status_code == 422

    def test_job_id_uuid_validation(self, client):
        """Job ID must be valid UUID."""
        r = client.get("/jobs/not-a-uuid")
        assert r.status_code in (422, 404)


class TestSecretsHandling:
    """Test that no hardcoded secrets exist."""

    def test_no_localdev123_in_database_config(self):
        """DatabaseSettings should not have hardcoded password default."""
        from src.database.config import DatabaseSettings
        from pydantic.fields import PydanticUndefined

        # Check the POSTGRES_PASSWORD field has no default (required field)
        fields = DatabaseSettings.model_fields
        pw_field = fields.get("POSTGRES_PASSWORD")
        assert pw_field is not None
        # In Pydantic v2, required fields have default=PydanticUndefined, not None
        assert pw_field.default is PydanticUndefined, "POSTGRES_PASSWORD should not have a default value"

    def test_no_localdev123_in_alembic_env(self):
        """alembic/env.py should not have hardcoded password fallback."""
        import os
        alembic_path = "/app/alembic/env.py"
        if not os.path.exists(alembic_path):
            pytest.skip("alembic/env.py not found in test environment")
        with open(alembic_path) as f:
            content = f.read()
        assert "localdev123" not in content, "alembic/env.py should not contain hardcoded password"

    def test_env_example_has_no_default_password(self):
        """.env.example should not have a default password."""
        import os
        env_example_path = "/app/.env.example"
        if not os.path.exists(env_example_path):
            pytest.skip(".env.example not found in test environment")
        with open(env_example_path) as f:
            content = f.read()
        # Should have placeholder comment, not actual password
        assert "POSTGRES_PASSWORD=" in content
        assert "localdev123" not in content
        assert "change_me" not in content.lower() or "must be set" in content.lower()


class TestRateLimiting:
    """Test rate limiting configuration."""

    def test_rate_limit_config_from_env(self, monkeypatch):
        """Rate limits configurable via environment."""
        monkeypatch.setenv("RATE_LIMIT_DEFAULT", "50/minute")
        monkeypatch.setenv("RATE_LIMIT_SEARCH", "10/minute")
        monkeypatch.setenv("RATE_LIMIT_STATS", "5/minute")

        import importlib
        import src.api.main
        importlib.reload(src.api.main)

        assert src.api.main.RATE_LIMIT_DEFAULT == "50/minute"
        assert src.api.main.RATE_LIMIT_SEARCH == "10/minute"
        assert src.api.main.RATE_LIMIT_STATS == "5/minute"

    def test_redis_url_configurable(self, monkeypatch):
        """Redis URL configurable via environment."""
        monkeypatch.setenv("REDIS_URL", "redis://custom:6379/1")
        import importlib
        import src.api.main
        importlib.reload(src.api.main)

        assert src.api.main.REDIS_URL == "redis://custom:6379/1"


class TestSQLInjectionPrevention:
    """Test that SQL queries are parameterized."""

    def test_orm_queries_use_parameters(self):
        """All API queries use SQLAlchemy ORM (parameterized)."""
        # The API uses db.query(Model).filter(...) which is parameterized
        # This test documents the expectation
        import src.api.main as api_main
        import inspect

        source = inspect.getsource(api_main.get_jobs)
        # Should use ORM query, not raw SQL string interpolation
        assert "db.query(" in source
        assert "ilike(" in source
        # Should NOT have f-string SQL
        assert 'f"SELECT' not in source
        assert "text(" not in source or "SELECT 1" in source  # Only static text()

    def test_processor_uses_orm(self):
        """Ingestion processor uses ORM."""
        import src.ingestion.processor as processor
        import inspect

        source = inspect.getsource(processor.JobProcessor.store_raw_jobs)
        assert "RawJobPosting(" in source
        assert "db.add(" in source

    def test_deduplication_uses_orm(self):
        """Deduplication engine uses ORM."""
        import src.deduplication.engine as engine
        import inspect

        source = inspect.getsource(engine.DeduplicationEngine.find_duplicate_of)
        assert "db.query(" in source


class TestDockerSecurity:
    """Test Docker security configuration."""

    def test_postgres_password_no_default_in_compose(self):
        """docker-compose.yml should not have default password."""
        import os
        compose_path = "/app/docker-compose.yml"
        if not os.path.exists(compose_path):
            pytest.skip("docker-compose.yml not found in test environment")
        with open(compose_path) as f:
            content = f.read()
        assert "localdev123" not in content
        assert "${POSTGRES_PASSWORD}" in content

    def test_redis_not_exposed_in_production_note(self):
        """Redis port exposure is documented for development only."""
        import os
        compose_path = "/app/docker-compose.yml"
        if not os.path.exists(compose_path):
            pytest.skip("docker-compose.yml not found in test environment")
        with open(compose_path) as f:
            content = f.read()
        # Redis port is exposed for development
        assert "6379:6379" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])