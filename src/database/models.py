"""SQLAlchemy models for database tables."""

from datetime import datetime, date
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey,
    Integer, Numeric, String, Text, Index
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# ============================================
# RAW DATA MODELS
# ============================================

class RawJobPosting(Base):
    """Raw job posting data as ingested from sources."""

    __tablename__ = "job_postings"
    __table_args__ = {"schema": "raw_data"}

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id = Column(String(255), nullable=False)
    source_name = Column(String(100), nullable=False, index=True)
    raw_data = Column(JSONB, nullable=False)
    ingested_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    processed = Column(Boolean, default=False, index=True)
    processing_errors = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================
# DIMENSION MODELS
# ============================================

class DimCompany(Base):
    """Company dimension table."""

    __tablename__ = "dim_company"
    __table_args__ = {"schema": "analytics"}

    company_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    company_name = Column(String(255), nullable=False, unique=True)
    company_name_normalized = Column(String(255), nullable=False, index=True)
    industry = Column(String(100))
    company_size = Column(String(50))
    company_url = Column(String(500))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class DimLocation(Base):
    """Location dimension table."""

    __tablename__ = "dim_location"
    __table_args__ = {"schema": "analytics"}

    location_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    city = Column(String(100), nullable=False)
    state_province = Column(String(100))
    country = Column(String(100), nullable=False, default="UAE")
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class DimSource(Base):
    """Data source dimension table."""

    __tablename__ = "dim_source"
    __table_args__ = {"schema": "analytics"}

    source_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_name = Column(String(100), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)
    source_url = Column(String(500))
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class DimCurrency(Base):
    """Currency dimension table."""

    __tablename__ = "dim_currency"
    __table_args__ = {"schema": "analytics"}

    currency_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    currency_code = Column(String(3), nullable=False, unique=True)
    currency_name = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class DimExperienceLevel(Base):
    """Experience level dimension table."""

    __tablename__ = "dim_experience_level"
    __table_args__ = {"schema": "analytics"}

    experience_level_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    level_name = Column(String(50), nullable=False, unique=True)
    level_description = Column(Text)
    sort_order = Column(Integer)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class DimEmploymentType(Base):
    """Employment type dimension table."""

    __tablename__ = "dim_employment_type"
    __table_args__ = {"schema": "analytics"}

    employment_type_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    type_name = Column(String(50), nullable=False, unique=True)
    type_description = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class DimSkill(Base):
    """Skill dimension table."""

    __tablename__ = "dim_skill"
    __table_args__ = {"schema": "analytics"}

    skill_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    skill_name = Column(String(100), nullable=False, unique=True)
    skill_name_normalized = Column(String(100), nullable=False, index=True)
    skill_category = Column(String(100), index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class DimTechnology(Base):
    """Technology dimension table."""

    __tablename__ = "dim_technology"
    __table_args__ = {"schema": "analytics"}

    technology_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    technology_name = Column(String(100), nullable=False, unique=True)
    technology_name_normalized = Column(String(100), nullable=False, index=True)
    technology_category = Column(String(100), index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ============================================
# FACT MODELS
# ============================================

class FactJobPosting(Base):
    """Normalized job posting fact table."""

    __tablename__ = "fact_job_posting"
    __table_args__ = {"schema": "analytics"}

    job_posting_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    raw_job_id = Column(PGUUID(as_uuid=True), ForeignKey("raw_data.job_postings.id"))

    # Job Details
    job_title = Column(String(255), nullable=False)
    job_description = Column(Text)
    posted_date = Column(Date, nullable=False, index=True)
    expiry_date = Column(Date)

    # Salary Information
    salary_min = Column(Numeric(12, 2))
    salary_max = Column(Numeric(12, 2))
    currency_id = Column(PGUUID(as_uuid=True), ForeignKey("analytics.dim_currency.currency_id"))
    salary_period = Column(String(20))

    # Job Classification
    experience_level_id = Column(PGUUID(as_uuid=True), ForeignKey("analytics.dim_experience_level.experience_level_id"))
    employment_type_id = Column(PGUUID(as_uuid=True), ForeignKey("analytics.dim_employment_type.employment_type_id"))

    # Foreign Keys
    company_id = Column(PGUUID(as_uuid=True), ForeignKey("analytics.dim_company.company_id"), nullable=False, index=True)
    location_id = Column(PGUUID(as_uuid=True), ForeignKey("analytics.dim_location.location_id"), nullable=False, index=True)
    source_id = Column(PGUUID(as_uuid=True), ForeignKey("analytics.dim_source.source_id"), nullable=False, index=True)

    # Extracted Fields
    extracted_skills = Column(JSONB)
    extracted_technologies = Column(JSONB)
    extracted_certifications = Column(JSONB)

    # Meta fields
    remote_allowed = Column(Boolean, default=False)
    visa_sponsorship = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, index=True)
    is_duplicate = Column(Boolean, default=False, index=True)
    duplicate_of_id = Column(PGUUID(as_uuid=True), ForeignKey("analytics.fact_job_posting.job_posting_id"))

    # Deduplication fingerprint
    content_hash = Column(String(64), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("DimCompany")
    location = relationship("DimLocation")
    source = relationship("DimSource")
    currency = relationship("DimCurrency")
    experience_level = relationship("DimExperienceLevel")
    employment_type = relationship("DimEmploymentType")


class FactJobPostingSnapshot(Base):
    """Job posting snapshot history for trend analysis."""

    __tablename__ = "fact_job_posting_snapshot"
    __table_args__ = {"schema": "analytics"}

    snapshot_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    job_posting_id = Column(PGUUID(as_uuid=True), ForeignKey("analytics.fact_job_posting.job_posting_id"), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    status = Column(String(20), nullable=False)
    view_count = Column(Integer, default=0)
    application_count = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    job_posting = relationship("FactJobPosting")
