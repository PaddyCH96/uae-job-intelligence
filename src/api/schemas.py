"""Pydantic schemas for API request/response models."""

from typing import Optional, List, Any
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, model_validator


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
    company_name: Optional[str] = None
    city: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def populate_joined_fields(cls, obj: Any) -> Any:
        # When Pydantic receives an ORM object, pull nested relationship values
        # into the flat fields expected by the response schema.
        if hasattr(obj, "company") and obj.company is not None:
            obj.__dict__.setdefault("company_name", obj.company.company_name)
        if hasattr(obj, "location") and obj.location is not None:
            obj.__dict__.setdefault("city", obj.location.city)
        return obj


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
