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

# Test database URL - requires POSTGRES_PASSWORD to be set in env for test DB
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://jobs_admin:${POSTGRES_PASSWORD}@localhost:5432/uae_jobs_test",
)

# Point the application settings at the test DB *before* any src.database import,
# because src/database/config.py builds a module-level engine at import time.
# Expand any environment variables in TEST_DATABASE_URL
TEST_DATABASE_URL_EXPANDED = os.path.expandvars(TEST_DATABASE_URL)

_parsed = TEST_DATABASE_URL_EXPANDED.replace("postgresql://", "")
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

        eng = sqlalchemy.create_engine(TEST_DATABASE_URL_EXPANDED)
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

    engine = sqlalchemy.create_engine(TEST_DATABASE_URL_EXPANDED)
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


@pytest.fixture(scope="session")
def seed_enriched_data():
    """Seed database with enriched test data for Phase 2/3 tests.
    
    This fixture ensures test data exists regardless of test execution order.
    It uses raw SQL to avoid ORM import issues and handles cleanup properly.
    """
    import sqlalchemy
    
    if not DB_AVAILABLE:
        pytest.skip("Test PostgreSQL database not reachable")
    
    engine = sqlalchemy.create_engine(TEST_DATABASE_URL_EXPANDED)
    
    with engine.connect() as conn:
        # Check if enriched data already exists
        result = conn.execute(
            sqlalchemy.text("SELECT COUNT(*) FROM analytics.fact_job_posting WHERE extracted_skills IS NOT NULL")
        )
        if result.scalar() >= 3:
            engine.dispose()
            return
        
        # Ensure dimension data exists for test database
        # First delete fact_job_posting records that reference old dimension IDs
        conn.execute(sqlalchemy.text("DELETE FROM analytics.fact_job_posting_snapshot"))
        conn.execute(sqlalchemy.text("UPDATE analytics.fact_job_posting SET is_duplicate = FALSE, duplicate_of_id = NULL"))
        conn.execute(sqlalchemy.text("DELETE FROM analytics.fact_job_posting"))
        conn.execute(sqlalchemy.text("DELETE FROM raw_data.job_postings"))
        conn.commit()
        
        # Use subqueries to get actual dimension IDs
        # Insert raw jobs with subqueries for dimension IDs
        conn.execute(sqlalchemy.text("""
            INSERT INTO raw_data.job_postings (source_id, source_name, raw_data, ingested_at, processed)
            VALUES 
            ('mock-001', 'MockJobBoard', 
             '{"title": "Senior Data Engineer", "company_name": "TechCorp UAE", "city": "Dubai", "country": "UAE", "description": "Looking for Senior Data Engineer with Python, SQL, AWS, and Spark. 5+ years experience.", "salary_min": 25000, "salary_max": 35000, "salary_currency": "AED", "employment_type": "Full-time", "experience_level": "Senior", "url": "https://mock.example.com/job/001"}',
             NOW(), false),
            ('mock-002', 'MockJobBoard',
             '{"title": "Machine Learning Engineer", "company_name": "AI Solutions Dubai", "city": "Abu Dhabi", "country": "UAE", "description": "ML Engineer. Skills: Python, TensorFlow, PyTorch, Docker, Kubernetes. Cloud experience preferred.", "salary_min": 30000, "salary_max": 45000, "salary_currency": "AED", "employment_type": "Full-time", "experience_level": "Mid", "url": "https://mock.example.com/job/002"}',
             NOW(), false),
            ('mock-003', 'MockJobBoard',
             '{"title": "Data Analyst", "company_name": "FinanceHub Abu Dhabi", "city": "Dubai", "country": "UAE", "description": "Data Analyst. SQL, Python, Tableau, Excel required. Good communication skills.", "salary_min": 15000, "salary_max": 22000, "salary_currency": "AED", "employment_type": "Full-time", "experience_level": "Entry", "url": "https://mock.example.com/job/003"}',
             NOW(), false),
            ('mock-004', 'MockJobBoard',
             '{"title": "DevOps Engineer", "company_name": "CloudFirst Technologies", "city": "Sharjah", "country": "UAE", "description": "DevOps role. AWS, Docker, Kubernetes, Terraform, Jenkins. CI/CD experience mandatory.", "salary_min": 22000, "salary_max": 32000, "salary_currency": "AED", "employment_type": "Full-time", "experience_level": "Mid", "url": "https://mock.example.com/job/004"}',
             NOW(), false),
            ('mock-005', 'MockJobBoard',
             '{"title": "AI Research Scientist", "company_name": "Innovation Labs Dubai", "city": "Dubai", "country": "UAE", "description": "Research Scientist. PhD preferred. Python, PyTorch, TensorFlow, NLP, Computer Vision.", "salary_min": 35000, "salary_max": 50000, "salary_currency": "AED", "employment_type": "Full-time", "experience_level": "Senior", "url": "https://mock.example.com/job/005"}',
             NOW(), false)
        """))
        conn.commit()
        
        # Insert fact job postings with enriched data using subqueries for dimension IDs
        conn.execute(sqlalchemy.text("""
            INSERT INTO analytics.fact_job_posting (
                raw_job_id, job_title, job_description, posted_date,
                salary_min, salary_max, currency_id,
                experience_level_id, employment_type_id,
                company_id, location_id, source_id,
                extracted_skills, extracted_technologies,
                content_hash, is_active
            )
            SELECT 
                r.id,
                r.raw_data->>'title',
                r.raw_data->>'description',
                CURRENT_DATE,
                (r.raw_data->>'salary_min')::numeric,
                (r.raw_data->>'salary_max')::numeric,
                (SELECT currency_id FROM analytics.dim_currency WHERE currency_code = 'AED' LIMIT 1),
                CASE 
                    WHEN r.raw_data->>'experience_level' = 'Senior' THEN (SELECT experience_level_id FROM analytics.dim_experience_level WHERE level_name = 'Senior' LIMIT 1)
                    WHEN r.raw_data->>'experience_level' = 'Mid' THEN (SELECT experience_level_id FROM analytics.dim_experience_level WHERE level_name = 'Mid' LIMIT 1)
                    ELSE (SELECT experience_level_id FROM analytics.dim_experience_level WHERE level_name = 'Entry' LIMIT 1)
                END,
                (SELECT employment_type_id FROM analytics.dim_employment_type WHERE type_name = 'Full-time' LIMIT 1),
                (SELECT company_id FROM analytics.dim_company WHERE company_name = r.raw_data->>'company_name' LIMIT 1),
                (SELECT location_id FROM analytics.dim_location WHERE city = r.raw_data->>'city' AND country = 'UAE' LIMIT 1),
                (SELECT source_id FROM analytics.dim_source WHERE source_name = 'MockJobBoard' LIMIT 1),
                CASE 
                    WHEN r.raw_data->>'description' LIKE '%Python%' AND r.raw_data->>'description' LIKE '%SQL%' 
                        THEN '["Python","SQL"]'::jsonb
                    WHEN r.raw_data->>'description' LIKE '%Python%' 
                        THEN '["Python"]'::jsonb
                    WHEN r.raw_data->>'description' LIKE '%SQL%' 
                        THEN '["SQL"]'::jsonb
                    ELSE '["General"]'::jsonb
                END,
                CASE 
                    WHEN r.raw_data->>'description' LIKE '%Spark%' AND r.raw_data->>'description' LIKE '%AWS%' 
                        THEN '["Spark","AWS"]'::jsonb
                    WHEN r.raw_data->>'description' LIKE '%Spark%' 
                        THEN '["Spark"]'::jsonb
                    WHEN r.raw_data->>'description' LIKE '%AWS%' 
                        THEN '["AWS"]'::jsonb
                    ELSE '[]'::jsonb
                END,
                md5((r.raw_data->>'title') || (r.raw_data->>'description')),
                true
            FROM raw_data.job_postings r
        """))
        
        # Mark raw jobs as processed
        conn.execute(sqlalchemy.text("UPDATE raw_data.job_postings SET processed = true"))
        conn.commit()
    
    engine.dispose()
