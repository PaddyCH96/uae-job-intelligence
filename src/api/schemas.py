"""Pydantic schemas for API request/response models."""

from typing import Optional, List, Any
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str


class JobPostingResponse(BaseModel):
    """Job posting response model."""
    model_config = ConfigDict(from_attributes=True)

    job_posting_id: UUID
    job_title: str
    job_description: Optional[str] = None
    posted_date: date
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    remote_allowed: bool
    visa_sponsorship: bool
    extracted_skills: Optional[Any] = None
    extracted_technologies: Optional[Any] = None


class JobSearchFilters(BaseModel):
    """Job search filter parameters."""
    company_name: Optional[str] = None
    city: Optional[str] = None
    min_salary: Optional[float] = Field(None, ge=0)
    max_salary: Optional[float] = Field(None, ge=0)
    remote_only: Optional[bool] = None
    visa_sponsorship: Optional[bool] = None
    posted_after: Optional[date] = None
    experience_level: Optional[str] = None
    employment_type: Optional[str] = None


class JobAggregation(BaseModel):
    """Aggregation result model."""
    name: str
    count: int


class CompanyResponse(BaseModel):
    """Company response model."""
    model_config = ConfigDict(from_attributes=True)

    company_id: UUID
    company_name: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    company_url: Optional[str] = None


class LocationResponse(BaseModel):
    """Location response model."""
    model_config = ConfigDict(from_attributes=True)

    location_id: UUID
    city: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
