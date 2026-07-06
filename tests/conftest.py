"""Shared pytest fixtures for the Phase 1 validation suite.

Environment strategy
--------------------
Pure-logic tests (text utils, salary parsing, dedup scoring) run with **no**
database and are always collected.

DB-backed tests use a real local PostgreSQL instance. They are gated behind the
``requires_db`` fixture, which skips (rather than errors) when the test database
is unreachable, so the suite still produces a meaningful pass/skip report in a
DB-less environment.

The test DB connection is taken from ``TEST_DATABASE_URL`` if set, otherwise a
sensible local default matching ``.env.example``.
"""

import os
import uuid

import pytest

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://jobs_admin:localdev123@localhost:5432/uae_jobs_test",
)

# Point the application settings at the test DB *before* any src.database import,
# because src/database/config.py builds a module-level engine at import time.
_parsed = TEST_DATABASE_URL.replace("postgresql://", "")
_creds, _hostpart = _parsed.split("@", 1)
_user, _pw = _creds.split(":", 1)
_hostport, _dbname = _hostpart.split("/", 1)
_host, _port = _hostport.split(":", 1)
os.environ.setdefault("POSTGRES_USER", _user)
os.environ.setdefault("POSTGRES_PASSWORD", _pw)
os.environ.setdefault("POSTGRES_HOST", _host)
os.environ.setdefault("POSTGRES_PORT", _port)
os.environ.setdefault("POSTGRES_DB", _dbname)


def _db_available() -> bool:
    try:
        import sqlalchemy

        eng = sqlalchemy.create_engine(TEST_DATABASE_URL)
        with eng.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        eng.dispose()
        return True
    except Exception:
        return False


DB_AVAILABLE = _db_available()


@pytest.fixture(scope="session")
def db_url():
    return TEST_DATABASE_URL


@pytest.fixture
def requires_db():
    """Skip a test cleanly when no test database is reachable."""
    if not DB_AVAILABLE:
        pytest.skip("Test PostgreSQL database not reachable")


@pytest.fixture
def db_session(requires_db):
    """A real DB session bound to the test database, rolled back after use."""
    import sqlalchemy
    from sqlalchemy.orm import sessionmaker

    engine = sqlalchemy.create_engine(TEST_DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        engine.dispose()


@pytest.fixture
def clean_facts(db_session):
    """Remove any job/fact rows created by a test (leave seed dims intact)."""
    import sqlalchemy

    yield db_session
    # Teardown: wipe test-created rows in FK-safe order.
    for stmt in (
        "DELETE FROM analytics.fact_job_posting_snapshot",
        "UPDATE analytics.fact_job_posting SET duplicate_of_id = NULL",
        "DELETE FROM analytics.fact_job_posting",
        "DELETE FROM raw_data.job_postings",
        "DELETE FROM analytics.dim_company WHERE company_name LIKE 'TEST_%'",
    ):
        try:
            db_session.execute(sqlalchemy.text(stmt))
        except Exception:
            db_session.rollback()
    db_session.commit()


@pytest.fixture
def sample_raw_job():
    return {
        "id": f"test_{uuid.uuid4().hex[:8]}",
        "job_title": "Data Engineer",
        "company": "TEST_Acme Analytics",
        "location": "Dubai",
        "description": "Build pipelines. Requirements: Python, SQL. Salary: AED 20,000 - 30,000.",
        "posted_date": "2026-07-01T00:00:00",
        "salary_range": "AED 20,000 - 30,000",
        "employment_type": "Full-time",
        "experience_level": "Mid Level",
        "remote_allowed": True,
        "url": "https://example.com/job/1",
    }
