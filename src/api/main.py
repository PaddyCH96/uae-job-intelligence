"""FastAPI backend for UAE Job Intelligence Platform."""

import os
import json
from typing import List, Optional
from datetime import date
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import sqlalchemy

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


@app.get("/aggregations/by-skill", response_model=List[JobAggregation])
@limiter.limit(RATE_LIMIT_DEFAULT) if limiter else lambda x: x
def aggregate_by_skill(
    request: Request,
    limit: int = Query(20, ge=1, le=MAX_AGGREGATION_LIMIT),
    db: Session = Depends(get_db)
):
    """
    Aggregate job counts by extracted skill.

    Args:
        limit: Number of top skills to return
        db: Database session

    Returns:
        List of skills with job counts
    """
    results = db.query(
        func.jsonb_array_elements_text(FactJobPosting.extracted_skills).label("name"),
        func.count(FactJobPosting.job_posting_id).label("count")
    ).filter(
        and_(
            FactJobPosting.is_active == True,
            FactJobPosting.is_duplicate == False,
            FactJobPosting.extracted_skills.isnot(None),
            FactJobPosting.extracted_skills != '[]'
        )
    ).group_by(
        func.jsonb_array_elements_text(FactJobPosting.extracted_skills)
    ).order_by(
        func.count(FactJobPosting.job_posting_id).desc()
    ).limit(limit).all()

    return [JobAggregation(name=r.name, count=r.count) for r in results]


@app.get("/aggregations/by-technology", response_model=List[JobAggregation])
@limiter.limit(RATE_LIMIT_DEFAULT) if limiter else lambda x: x
def aggregate_by_technology(
    request: Request,
    limit: int = Query(20, ge=1, le=MAX_AGGREGATION_LIMIT),
    db: Session = Depends(get_db)
):
    """
    Aggregate job counts by extracted technology.

    Args:
        limit: Number of top technologies to return
        db: Database session

    Returns:
        List of technologies with job counts
    """
    results = db.query(
        func.jsonb_array_elements_text(FactJobPosting.extracted_technologies).label("name"),
        func.count(FactJobPosting.job_posting_id).label("count")
    ).filter(
        and_(
            FactJobPosting.is_active == True,
            FactJobPosting.is_duplicate == False,
            FactJobPosting.extracted_technologies.isnot(None),
            FactJobPosting.extracted_technologies != '[]'
        )
    ).group_by(
        func.jsonb_array_elements_text(FactJobPosting.extracted_technologies)
    ).order_by(
        func.count(FactJobPosting.job_posting_id).desc()
    ).limit(limit).all()

    return [JobAggregation(name=r.name, count=r.count) for r in results]


@app.get("/aggregations/by-industry", response_model=List[JobAggregation])
@limiter.limit(RATE_LIMIT_DEFAULT) if limiter else lambda x: x
def aggregate_by_industry(
    request: Request,
    limit: int = Query(20, ge=1, le=MAX_AGGREGATION_LIMIT),
    db: Session = Depends(get_db)
):
    """
    Aggregate job counts by industry.

    Args:
        limit: Number of top industries to return
        db: Database session

    Returns:
        List of industries with job counts
    """
    results = db.query(
        DimCompany.industry.label("name"),
        func.count(FactJobPosting.job_posting_id).label("count")
    ).join(
        FactJobPosting
    ).filter(
        and_(
            FactJobPosting.is_active == True,
            FactJobPosting.is_duplicate == False,
            DimCompany.industry.isnot(None)
        )
    ).group_by(
        DimCompany.industry
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


# Phase 6 Endpoints: ATS Keywords, Contacts, Recommendations

@app.get("/jobs/{job_id}/ats-keywords")
async def get_job_ats_keywords(job_id: UUID, db: Session = Depends(get_db)):
    """Get ATS keywords for a specific job."""
    result = db.execute(
        sqlalchemy.text("""
            SELECT * FROM analytics.fact_job_ats_keywords 
            WHERE job_posting_id = :job_id
        """),
        {"job_id": str(job_id)}
    )
    row = result.fetchone()
    if not row:
        return {"message": "No ATS keywords found", "keywords": {}}
    return {
        "job_id": str(row.job_posting_id),
        "hard_skills": row.hard_skills or [],
        "soft_skills": row.soft_skills or [],
        "action_verbs": row.action_verbs or [],
        "certifications": row.certifications or [],
        "industry_terms": row.industry_terms or []
    }


@app.post("/jobs/{job_id}/ats-keywords")
async def extract_job_ats_keywords(job_id: UUID, db: Session = Depends(get_db)):
    """Extract and store ATS keywords for a job."""
    from src.intelligence.llm.ats_extractor import ATSKeywordExtractor
    
    # Get job details
    result = db.execute(
        sqlalchemy.text("""
            SELECT job_title, job_description, company_id 
            FROM analytics.fact_job_posting 
            WHERE job_posting_id = :job_id
        """),
        {"job_id": str(job_id)}
    )
    job = result.fetchone()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get company name
    company_result = db.execute(
        sqlalchemy.text("SELECT company_name FROM analytics.dim_company WHERE company_id = :id"),
        {"id": job.company_id}
    )
    company = company_result.fetchone()
    
    extractor = ATSKeywordExtractor()
    keywords = await extractor.extract({
        "title": job.job_title,
        "company_name": company.company_name if company else "",
        "description": job.job_description
    })
    
    # Store keywords
    db.execute(
        sqlalchemy.text("""
            INSERT INTO analytics.fact_job_ats_keywords (job_posting_id, hard_skills, soft_skills, action_verbs, certifications, industry_terms)
            VALUES (:job_id, :hard_skills, :soft_skills, :action_verbs, :certifications, :industry_terms)
            ON CONFLICT (job_posting_id) DO UPDATE SET
                hard_skills = EXCLUDED.hard_skills,
                soft_skills = EXCLUDED.soft_skills,
                action_verbs = EXCLUDED.action_verbs,
                certifications = EXCLUDED.certifications,
                industry_terms = EXCLUDED.industry_terms
        """),
        {
            "job_id": str(job_id),
            "hard_skills": json.dumps(keywords.get("hard_skills", [])),
            "soft_skills": json.dumps(keywords.get("soft_skills", [])),
            "action_verbs": json.dumps(keywords.get("action_verbs", [])),
            "certifications": json.dumps(keywords.get("certifications", [])),
            "industry_terms": json.dumps(keywords.get("industry_terms", []))
        }
    )
    db.commit()
    
    return {"message": "ATS keywords extracted", "keywords": keywords}


@app.get("/companies/{company_id}/contacts")
async def get_company_contacts(company_id: UUID, db: Session = Depends(get_db)):
    """Get contacts for a company."""
    result = db.execute(
        sqlalchemy.text("""
            SELECT * FROM analytics.dim_company_contacts 
            WHERE company_id = :company_id
        """),
        {"company_id": str(company_id)}
    )
    contacts = result.fetchall()
    return [
        {
            "id": str(c.id),
            "name": c.contact_name,
            "email": c.email,
            "confidence": float(c.email_confidence) if c.email_confidence else 0,
            "linkedin": c.linkedin_url,
            "position": c.position,
            "source": c.source
        }
        for c in contacts
    ]


@app.get("/recommendations")
async def get_recommendations(user_id: str = "default", limit: int = 10, db: Session = Depends(get_db)):
    """Get job recommendations for a user."""
    result = db.execute(
        sqlalchemy.text("""
            SELECT r.*, j.job_title, j.company_id, l.city, j.salary_min, j.salary_max, 
                   rj.raw_data->>'url' as url
            FROM analytics.job_recommendations r
            JOIN analytics.fact_job_posting j ON r.job_posting_id = j.job_posting_id
            LEFT JOIN analytics.dim_location l ON j.location_id = l.location_id
            LEFT JOIN raw_data.job_postings rj ON j.raw_job_id = rj.id
            WHERE r.user_id = :user_id 
            AND r.expires_at > CURRENT_TIMESTAMP
            ORDER BY r.score DESC
            LIMIT :limit
        """),
        {"user_id": user_id, "limit": limit}
    )
    recs = result.fetchall()
    
    recommendations = []
    for rec in recs:
        # Get company name
        company_result = db.execute(
            sqlalchemy.text("SELECT company_name FROM analytics.dim_company WHERE company_id = :id"),
            {"id": rec.company_id}
        )
        company = company_result.fetchone()
        
        recommendations.append({
            "job_id": str(rec.job_posting_id),
            "title": rec.job_title,
            "company_name": company.company_name if company else "Unknown",
            "city": rec.city,
            "salary_range": f"AED {rec.salary_min:,.0f} - {rec.salary_max:,.0f}" if rec.salary_min and rec.salary_max else "Not specified",
            "score": float(rec.score),
            "url": rec.url
        })
    
    return recommendations


@app.post("/recommendations/generate")
async def generate_recommendations(user_id: str = "default", db: Session = Depends(get_db)):
    """Generate new recommendations for a user."""
    from src.intelligence.recommendations.engine import RecommendationEngine
    
    engine = RecommendationEngine()
    
    # Get recent jobs
    result = db.execute(
        sqlalchemy.text("""
            SELECT j.*, c.company_name, l.city, rj.raw_data->>'url' as url
            FROM analytics.fact_job_posting j
            LEFT JOIN analytics.dim_company c ON j.company_id = c.company_id
            LEFT JOIN analytics.dim_location l ON j.location_id = l.location_id
            LEFT JOIN raw_data.job_postings rj ON j.raw_job_id = rj.id
            WHERE j.is_active = true AND j.is_duplicate = false
            ORDER BY j.posted_date DESC
            LIMIT 100
        """)
    )
    jobs = result.fetchall()
    
    if not jobs:
        return {"message": "No jobs available for recommendations"}
    
    # Convert to dict format
    jobs_dict = []
    for job in jobs:
        jobs_dict.append({
            "job_posting_id": str(job.job_posting_id),
            "title": job.job_title,
            "company_name": job.company_name,
            "city": job.city,
            "salary_min": float(job.salary_min) if job.salary_min else None,
            "salary_max": float(job.salary_max) if job.salary_max else None,
            "posted_date": job.posted_date.isoformat() if job.posted_date else None,
            "url": job.url,
            "extracted_skills": []  # Would need to join with skills table
        })
    
    # Default user profile
    user_profile = {
        "skills": ["Python", "SQL", "Data Analysis"],
        "experience_years": 3,
        "expected_salary_min": 15000,
        "expected_salary_max": 30000,
        "preferred_cities": ["Dubai", "Abu Dhabi"]
    }
    
    # Get recommendations
    top_10 = engine.rank_jobs(jobs_dict, user_profile)
    
    # Store recommendations
    for i, rec in enumerate(top_10, 1):
        db.execute(
            sqlalchemy.text("""
                INSERT INTO analytics.job_recommendations (user_id, job_posting_id, score, rank, expires_at)
                VALUES (:user_id, :job_id, :score, :rank, CURRENT_TIMESTAMP + INTERVAL '1 day')
            """),
            {
                "user_id": user_id,
                "job_id": rec["job_posting_id"],
                "score": rec["score"],
                "rank": i
            }
        )
    
    db.commit()
    return {"message": f"Generated {len(top_10)} recommendations", "count": len(top_10)}


@app.post("/enrich/batch-ats")
async def batch_enrich_ats_keywords(limit: int = 10, db: Session = Depends(get_db)):
    """Batch extract ATS keywords for multiple jobs."""
    from src.intelligence.llm.ats_extractor import ATSKeywordExtractor
    
    extractor = ATSKeywordExtractor()
    
    # Get jobs without ATS keywords
    result = db.execute(
        sqlalchemy.text("""
            SELECT j.job_posting_id, j.job_title, j.job_description, j.company_id
            FROM analytics.fact_job_posting j
            LEFT JOIN analytics.fact_job_ats_keywords a ON j.job_posting_id = a.job_posting_id
            WHERE a.id IS NULL AND j.is_active = true
            LIMIT :limit
        """),
        {"limit": limit}
    )
    jobs = result.fetchall()
    
    enriched = 0
    for job in jobs:
        try:
            # Get company name
            company_result = db.execute(
                sqlalchemy.text("SELECT company_name FROM analytics.dim_company WHERE company_id = :id"),
                {"id": job.company_id}
            )
            company = company_result.fetchone()
            
            keywords = await extractor.extract({
                "title": job.job_title,
                "company_name": company.company_name if company else "",
                "description": job.job_description
            })
            
            db.execute(
                sqlalchemy.text("""
                    INSERT INTO analytics.fact_job_ats_keywords (job_posting_id, hard_skills, soft_skills, action_verbs, certifications, industry_terms)
                    VALUES (:job_id, :hard_skills, :soft_skills, :action_verbs, :certifications, :industry_terms)
                """),
                {
                    "job_id": str(job.job_posting_id),
                    "hard_skills": json.dumps(keywords.get("hard_skills", [])),
                    "soft_skills": json.dumps(keywords.get("soft_skills", [])),
                    "action_verbs": json.dumps(keywords.get("action_verbs", [])),
                    "certifications": json.dumps(keywords.get("certifications", [])),
                    "industry_terms": json.dumps(keywords.get("industry_terms", []))
                }
            )
            enriched += 1
        except Exception as e:
            logger.error(f"Failed to enrich job {job.job_posting_id}: {e}")
            continue
    
    db.commit()
    return {"message": f"Enriched {enriched} jobs with ATS keywords", "count": enriched}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
