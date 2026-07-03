"""FastAPI backend for UAE Job Intelligence Platform."""

from typing import List, Optional
from datetime import date

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
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

# Initialize FastAPI app
app = FastAPI(
    title="UAE Job Intelligence API",
    description="API for accessing UAE job market intelligence data",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", service="uae-jobs-api")


@app.get("/jobs", response_model=List[JobPostingResponse])
def get_jobs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    company_name: Optional[str] = Query(None, description="Filter by company name"),
    city: Optional[str] = Query(None, description="Filter by city"),
    min_salary: Optional[float] = Query(None, description="Minimum salary"),
    remote_only: Optional[bool] = Query(None, description="Remote jobs only"),
    visa_sponsorship: Optional[bool] = Query(None, description="Visa sponsorship offered"),
    posted_after: Optional[date] = Query(None, description="Posted after date (YYYY-MM-DD)"),
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
        remote_only: Show only remote jobs
        visa_sponsorship: Show only jobs with visa sponsorship
        posted_after: Show jobs posted after this date
        db: Database session

    Returns:
        List of job postings
    """
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

    if remote_only is not None and remote_only:
        query = query.filter(FactJobPosting.remote_allowed == True)

    if visa_sponsorship is not None and visa_sponsorship:
        query = query.filter(FactJobPosting.visa_sponsorship == True)

    if posted_after:
        query = query.filter(FactJobPosting.posted_date >= posted_after)

    # Order by most recent
    query = query.order_by(FactJobPosting.posted_date.desc())

    # Pagination
    jobs = query.offset(skip).limit(limit).all()

    return jobs


@app.get("/jobs/{job_id}", response_model=JobPostingResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
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


@app.get("/jobs/search", response_model=List[JobPostingResponse])
def search_jobs(
    q: str = Query(..., min_length=2, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Full-text search across job postings.

    Args:
        q: Search query string
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


@app.get("/aggregations/by-company", response_model=List[JobAggregation])
def aggregate_by_company(
    limit: int = Query(20, ge=1, le=100),
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
def aggregate_by_city(
    limit: int = Query(20, ge=1, le=100),
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
def get_stats(db: Session = Depends(get_db)):
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
