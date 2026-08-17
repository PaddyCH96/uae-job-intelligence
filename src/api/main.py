"""FastAPI backend for UAE Job Intelligence Platform."""

import os
from typing import List, Optional
from datetime import date
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from src.database import get_db, FactJobPosting, DimCompany, DimLocation
from src.api.schemas import (
    JobPostingResponse,
    JobSearchFilters,
    JobAggregation,
    HealthResponse
)
from src.utils.logger import logger
from src.database.config import db_settings

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis

# Constants for input validation
MAX_SEARCH_QUERY_LENGTH = 200
MAX_FILTER_STRING_LENGTH = 100
MAX_PAGE_SIZE = 1000
MAX_AGGREGATION_LIMIT = 100
MAX_SALARY = 1_000_000  # 1M AED - reasonable upper bound
MIN_SALARY = 0
MIN_POSTED_DATE = date(2020, 1, 1)  # Data starts from 2020
MAX_POSTED_DATE = date(2030, 12, 31)  # Reasonable future bound

# Rate limit configuration
RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")
RATE_LIMIT_SEARCH = os.getenv("RATE_LIMIT_SEARCH", "30/minute")
RATE_LIMIT_STATS = os.getenv("RATE_LIMIT_STATS", "10/minute")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize FastAPI app
app = FastAPI(
    title="UAE Job Intelligence API",
    description="API for accessing UAE job market intelligence data",
    version="1.0.0",
)

# CORS configuration - environment-driven allowlist
# In production, CORS_ORIGINS must be explicitly set (comma-separated)
# In development, defaults to common local origins
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    allow_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
else:
    # Development defaults - only used when CORS_ORIGINS is not set
    allow_origins = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

# Credentials only allowed when explicit origins are configured (never with wildcard)
allow_credentials = bool(cors_origins_env)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Rate limiting setup
# Use Redis for distributed rate limiting across multiple API instances
# Falls back to in-memory if Redis unavailable (development only)
try:
    redis_client = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    redis_client.ping()
    limiter = Limiter(key_func=get_remote_address, storage_uri=REDIS_URL)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("Rate limiting enabled with Redis backend")
except Exception as e:
    logger.warning(f"Redis unavailable, rate limiting disabled: {e}")
    limiter = None


def validate_salary_range(min_salary: Optional[float], max_salary: Optional[float]) -> None:
    """Validate salary range parameters."""
    if min_salary is not None and max_salary is not None:
        if min_salary > max_salary:
            raise HTTPException(
                status_code=422,
                detail="min_salary must be less than or equal to max_salary"
            )


def validate_date_range(posted_after: Optional[date], posted_before: Optional[date]) -> None:
    """Validate date range parameters."""
    if posted_after and posted_before and posted_after > posted_before:
        raise HTTPException(
            status_code=422,
            detail="posted_after must be before or equal to posted_before"
        )


@app.get("/health", response_model=HealthResponse)
@limiter.limit(RATE_LIMIT_DEFAULT) if limiter else lambda x: x
def health_check(request: Request):
    """Health check endpoint."""
    return HealthResponse(status="healthy", service="uae-jobs-api")


@app.get("/jobs", response_model=List[JobPostingResponse])
@limiter.limit(RATE_LIMIT_DEFAULT) if limiter else lambda x: x
def get_jobs(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=MAX_PAGE_SIZE, description="Number of records to return"),
    company_name: Optional[str] = Query(None, max_length=MAX_FILTER_STRING_LENGTH, description="Filter by company name"),
    city: Optional[str] = Query(None, max_length=MAX_FILTER_STRING_LENGTH, description="Filter by city"),
    min_salary: Optional[float] = Query(None, ge=MIN_SALARY, le=MAX_SALARY, description="Minimum salary"),
    max_salary: Optional[float] = Query(None, ge=MIN_SALARY, le=MAX_SALARY, description="Maximum salary"),
    remote_only: Optional[bool] = Query(None, description="Remote jobs only"),
    visa_sponsorship: Optional[bool] = Query(None, description="Visa sponsorship offered"),
    posted_after: Optional[date] = Query(None, ge=MIN_POSTED_DATE, le=MAX_POSTED_DATE, description="Posted after date (YYYY-MM-DD)"),
    posted_before: Optional[date] = Query(None, ge=MIN_POSTED_DATE, le=MAX_POSTED_DATE, description="Posted before date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Get job postings with filters.

    Args:
        skip: Pagination offset
        limit: Number of results
        company_name: Filter by company
        city: Filter by city
        min_salary: Minimum salary filter
        max_salary: Maximum salary filter
        remote_only: Show only remote jobs
        visa_sponsorship: Show only jobs with visa sponsorship
        posted_after: Show jobs posted after this date
        posted_before: Show jobs posted before this date
        db: Database session

    Returns:
        List of job postings
    """
    validate_salary_range(min_salary, max_salary)
    validate_date_range(posted_after, posted_before)

    query = db.query(FactJobPosting).join(
        DimCompany
    ).join(
        DimLocation
    ).filter(
        and_(
            FactJobPosting.is_active == True,
            FactJobPosting.is_duplicate == False
        )
    )

    # Apply filters
    if company_name:
        query = query.filter(DimCompany.company_name.ilike(f"%{company_name}%"))

    if city:
        query = query.filter(DimLocation.city.ilike(f"%{city}%"))

    if min_salary is not None:
        query = query.filter(FactJobPosting.salary_min >= min_salary)

    if max_salary is not None:
        query = query.filter(FactJobPosting.salary_max <= max_salary)

    if remote_only is not None and remote_only:
        query = query.filter(FactJobPosting.remote_allowed == True)

    if visa_sponsorship is not None and visa_sponsorship:
        query = query.filter(FactJobPosting.visa_sponsorship == True)

    if posted_after:
        query = query.filter(FactJobPosting.posted_date >= posted_after)

    if posted_before:
        query = query.filter(FactJobPosting.posted_date <= posted_before)

    # Order by most recent
    query = query.order_by(FactJobPosting.posted_date.desc())

    # Pagination
    jobs = query.offset(skip).limit(limit).all()

    return jobs


@app.get("/jobs/search", response_model=List[JobPostingResponse])
@limiter.limit(RATE_LIMIT_SEARCH) if limiter else lambda x: x
def search_jobs(
    request: Request,
    q: str = Query(..., min_length=2, max_length=MAX_SEARCH_QUERY_LENGTH, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Full-text search across job postings.

    Args:
        q: Search query string (2-200 characters)
        skip: Pagination offset
        limit: Number of results
        db: Database session

    Returns:
        List of matching job postings
    """
    search_term = f"%{q}%"

    jobs = db.query(FactJobPosting).join(DimCompany).filter(
        and_(
            FactJobPosting.is_active == True,
            FactJobPosting.is_duplicate == False,
            or_(
                FactJobPosting.job_title.ilike(search_term),
                FactJobPosting.job_description.ilike(search_term),
                DimCompany.company_name.ilike(search_term)
            )
        )
    ).order_by(
        FactJobPosting.posted_date.desc()
    ).offset(skip).limit(limit).all()

    return jobs


@app.get("/jobs/{job_id}", response_model=JobPostingResponse)
@limiter.limit(RATE_LIMIT_DEFAULT) if limiter else lambda x: x
def get_job(
    request: Request,
    job_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get single job posting by ID.

    Args:
        job_id: Job posting UUID
        db: Database session

    Returns:
        Job posting details

    Raises:
        HTTPException: If job not found
    """
    job = db.query(FactJobPosting).filter(
        FactJobPosting.job_posting_id == job_id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@app.get("/aggregations/by-company", response_model=List[JobAggregation])
@limiter.limit(RATE_LIMIT_DEFAULT) if limiter else lambda x: x
def aggregate_by_company(
    request: Request,
    limit: int = Query(20, ge=1, le=MAX_AGGREGATION_LIMIT),
    db: Session = Depends(get_db)
):
    """
    Aggregate job counts by company.

    Args:
        limit: Number of top companies to return
        db: Database session

    Returns:
        List of companies with job counts
    """
    results = db.query(
        DimCompany.company_name.label("name"),
        func.count(FactJobPosting.job_posting_id).label("count")
    ).join(
        FactJobPosting
    ).filter(
        and_(
            FactJobPosting.is_active == True,
            FactJobPosting.is_duplicate == False
        )
    ).group_by(
        DimCompany.company_name
    ).order_by(
        func.count(FactJobPosting.job_posting_id).desc()
    ).limit(limit).all()

    return [JobAggregation(name=r.name, count=r.count) for r in results]


@app.get("/aggregations/by-city", response_model=List[JobAggregation])
@limiter.limit(RATE_LIMIT_DEFAULT) if limiter else lambda x: x
def aggregate_by_city(
    request: Request,
    limit: int = Query(20, ge=1, le=MAX_AGGREGATION_LIMIT),
    db: Session = Depends(get_db)
):
    """
    Aggregate job counts by city.

    Args:
        limit: Number of top cities to return
        db: Database session

    Returns:
        List of cities with job counts
    """
    results = db.query(
        DimLocation.city.label("name"),
        func.count(FactJobPosting.job_posting_id).label("count")
    ).join(
        FactJobPosting
    ).filter(
        and_(
            FactJobPosting.is_active == True,
            FactJobPosting.is_duplicate == False
        )
    ).group_by(
        DimLocation.city
    ).order_by(
        func.count(FactJobPosting.job_posting_id).desc()
    ).limit(limit).all()

    return [JobAggregation(name=r.name, count=r.count) for r in results]


@app.get("/stats")
@limiter.limit(RATE_LIMIT_STATS) if limiter else lambda x: x
def get_stats(request: Request, db: Session = Depends(get_db)):
    """
    Get platform statistics.

    Args:
        db: Database session

    Returns:
        Dictionary of statistics
    """
    total_jobs = db.query(FactJobPosting).count()
    active_jobs = db.query(FactJobPosting).filter(
        and_(
            FactJobPosting.is_active == True,
            FactJobPosting.is_duplicate == False
        )
    ).count()
    duplicate_jobs = db.query(FactJobPosting).filter(
        FactJobPosting.is_duplicate == True
    ).count()
    total_companies = db.query(DimCompany).count()
    jobs_with_salary = db.query(FactJobPosting).filter(
        FactJobPosting.salary_min.isnot(None)
    ).count()
    remote_jobs = db.query(FactJobPosting).filter(
        and_(
            FactJobPosting.is_active == True,
            FactJobPosting.remote_allowed == True
        )
    ).count()
    visa_jobs = db.query(FactJobPosting).filter(
        and_(
            FactJobPosting.is_active == True,
            FactJobPosting.visa_sponsorship == True
        )
    ).count()

    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "duplicate_jobs": duplicate_jobs,
        "total_companies": total_companies,
        "jobs_with_salary_info": jobs_with_salary,
        "remote_jobs": remote_jobs,
        "visa_sponsorship_jobs": visa_jobs,
        "deduplication_rate": round(duplicate_jobs / total_jobs * 100, 2) if total_jobs > 0 else 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
