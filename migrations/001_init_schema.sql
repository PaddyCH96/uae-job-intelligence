-- UAE Job Intelligence Platform - Database Schema
-- Phase 1: Core Tables for Data Collection and Normalization

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS raw_data;
CREATE SCHEMA IF NOT EXISTS analytics;

-- ============================================
-- RAW DATA SCHEMA
-- ============================================

-- Raw job postings (as ingested)
CREATE TABLE raw_data.job_postings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id VARCHAR(255) NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    raw_data JSONB NOT NULL,
    ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    processing_errors TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_raw_job_postings_source ON raw_data.job_postings(source_name);
CREATE INDEX idx_raw_job_postings_processed ON raw_data.job_postings(processed);
CREATE INDEX idx_raw_job_postings_ingested_at ON raw_data.job_postings(ingested_at DESC);
CREATE INDEX idx_raw_job_postings_raw_data ON raw_data.job_postings USING gin(raw_data);

-- ============================================
-- ANALYTICS SCHEMA - DIMENSION TABLES
-- ============================================

-- Companies
CREATE TABLE analytics.dim_company (
    company_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(255) NOT NULL UNIQUE,
    company_name_normalized VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    company_size VARCHAR(50),
    company_url VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_company_name_normalized ON analytics.dim_company(company_name_normalized);

-- Locations
CREATE TABLE analytics.dim_location (
    location_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    city VARCHAR(100) NOT NULL,
    state_province VARCHAR(100),
    country VARCHAR(100) NOT NULL DEFAULT 'UAE',
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(city, state_province, country)
);

CREATE INDEX idx_dim_location_city ON analytics.dim_location(city);

-- Data Sources
CREATE TABLE analytics.dim_source (
    source_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(100) NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL,
    source_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_source_active ON analytics.dim_source(is_active);

-- Currencies
CREATE TABLE analytics.dim_currency (
    currency_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    currency_code VARCHAR(3) NOT NULL UNIQUE,
    currency_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Experience Levels
CREATE TABLE analytics.dim_experience_level (
    experience_level_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level_name VARCHAR(50) NOT NULL UNIQUE,
    level_description TEXT,
    sort_order INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Employment Types
CREATE TABLE analytics.dim_employment_type (
    employment_type_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type_name VARCHAR(50) NOT NULL UNIQUE,
    type_description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Skills
CREATE TABLE analytics.dim_skill (
    skill_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    skill_name VARCHAR(100) NOT NULL UNIQUE,
    skill_name_normalized VARCHAR(100) NOT NULL,
    skill_category VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_skill_category ON analytics.dim_skill(skill_category);
CREATE INDEX idx_dim_skill_name_normalized ON analytics.dim_skill(skill_name_normalized);

-- Technologies
CREATE TABLE analytics.dim_technology (
    technology_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    technology_name VARCHAR(100) NOT NULL UNIQUE,
    technology_name_normalized VARCHAR(100) NOT NULL,
    technology_category VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_technology_category ON analytics.dim_technology(technology_category);
CREATE INDEX idx_dim_technology_name_normalized ON analytics.dim_technology(technology_name_normalized);

-- ============================================
-- ANALYTICS SCHEMA - FACT TABLES
-- ============================================

-- Job Postings (Normalized)
CREATE TABLE analytics.fact_job_posting (
    job_posting_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    raw_job_id UUID REFERENCES raw_data.job_postings(id),

    -- Job Details
    job_title VARCHAR(255) NOT NULL,
    job_description TEXT,
    posted_date DATE NOT NULL,
    expiry_date DATE,

    -- Salary Information
    salary_min DECIMAL(12, 2),
    salary_max DECIMAL(12, 2),
    currency_id UUID REFERENCES analytics.dim_currency(currency_id),
    salary_period VARCHAR(20), -- hourly, monthly, annual

    -- Job Classification
    experience_level_id UUID REFERENCES analytics.dim_experience_level(experience_level_id),
    employment_type_id UUID REFERENCES analytics.dim_employment_type(employment_type_id),

    -- Foreign Keys
    company_id UUID NOT NULL REFERENCES analytics.dim_company(company_id),
    location_id UUID NOT NULL REFERENCES analytics.dim_location(location_id),
    source_id UUID NOT NULL REFERENCES analytics.dim_source(source_id),

    -- Extracted Fields (JSON for flexibility)
    extracted_skills JSONB,
    extracted_technologies JSONB,
    extracted_certifications JSONB,

    -- Meta fields
    remote_allowed BOOLEAN DEFAULT FALSE,
    visa_sponsorship BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of_id UUID REFERENCES analytics.fact_job_posting(job_posting_id),

    -- Deduplication fingerprint
    content_hash VARCHAR(64) NOT NULL,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Ensure duplicate records reference parent
    CONSTRAINT check_duplicate_reference CHECK (
        (is_duplicate = FALSE AND duplicate_of_id IS NULL) OR
        (is_duplicate = TRUE AND duplicate_of_id IS NOT NULL)
    )
);

-- Indexes for fact_job_posting
CREATE INDEX idx_fact_job_posting_company ON analytics.fact_job_posting(company_id);
CREATE INDEX idx_fact_job_posting_location ON analytics.fact_job_posting(location_id);
CREATE INDEX idx_fact_job_posting_source ON analytics.fact_job_posting(source_id);
CREATE INDEX idx_fact_job_posting_posted_date ON analytics.fact_job_posting(posted_date DESC);
CREATE INDEX idx_fact_job_posting_content_hash ON analytics.fact_job_posting(content_hash);
CREATE INDEX idx_fact_job_posting_is_duplicate ON analytics.fact_job_posting(is_duplicate);
CREATE INDEX idx_fact_job_posting_active ON analytics.fact_job_posting(is_active);
CREATE INDEX idx_fact_job_posting_skills ON analytics.fact_job_posting USING gin(extracted_skills);
CREATE INDEX idx_fact_job_posting_technologies ON analytics.fact_job_posting USING gin(extracted_technologies);

-- Job Posting Snapshot History (for trend analysis)
CREATE TABLE analytics.fact_job_posting_snapshot (
    snapshot_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_posting_id UUID NOT NULL REFERENCES analytics.fact_job_posting(job_posting_id),
    snapshot_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL, -- active, expired, filled, removed
    view_count INTEGER DEFAULT 0,
    application_count INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(job_posting_id, snapshot_date)
);

CREATE INDEX idx_fact_job_posting_snapshot_date ON analytics.fact_job_posting_snapshot(snapshot_date DESC);
CREATE INDEX idx_fact_job_posting_snapshot_job ON analytics.fact_job_posting_snapshot(job_posting_id);

-- ============================================
-- SEED DATA
-- ============================================

-- Common currencies
INSERT INTO analytics.dim_currency (currency_code, currency_name) VALUES
('AED', 'United Arab Emirates Dirham'),
('USD', 'United States Dollar'),
('EUR', 'Euro'),
('GBP', 'British Pound');

-- Experience levels
INSERT INTO analytics.dim_experience_level (level_name, level_description, sort_order) VALUES
('Entry Level', '0-2 years of experience', 1),
('Junior', '1-3 years of experience', 2),
('Mid Level', '3-5 years of experience', 3),
('Senior', '5-10 years of experience', 4),
('Lead', '8+ years with team leadership', 5),
('Principal', '10+ years, senior technical leadership', 6),
('Executive', 'C-level or VP positions', 7);

-- Employment types
INSERT INTO analytics.dim_employment_type (type_name, type_description) VALUES
('Full-time', 'Permanent full-time position'),
('Part-time', 'Permanent part-time position'),
('Contract', 'Fixed-term contract'),
('Temporary', 'Temporary position'),
('Internship', 'Internship or trainee position'),
('Freelance', 'Freelance or consultant position');

-- Common UAE cities
INSERT INTO analytics.dim_location (city, state_province, country, latitude, longitude) VALUES
('Dubai', 'Dubai', 'UAE', 25.2048, 55.2708),
('Abu Dhabi', 'Abu Dhabi', 'UAE', 24.4539, 54.3773),
('Sharjah', 'Sharjah', 'UAE', 25.3463, 55.4209),
('Ajman', 'Ajman', 'UAE', 25.4052, 55.5136),
('Ras Al Khaimah', 'Ras Al Khaimah', 'UAE', 25.7895, 55.9432),
('Fujairah', 'Fujairah', 'UAE', 25.1288, 56.3265),
('Umm Al Quwain', 'Umm Al Quwain', 'UAE', 25.5647, 55.5550);

-- ============================================
-- FUNCTIONS AND TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables
CREATE TRIGGER update_raw_job_postings_updated_at
    BEFORE UPDATE ON raw_data.job_postings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dim_company_updated_at
    BEFORE UPDATE ON analytics.dim_company
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fact_job_posting_updated_at
    BEFORE UPDATE ON analytics.fact_job_posting
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- Active jobs with all details
CREATE OR REPLACE VIEW analytics.v_active_jobs AS
SELECT
    j.job_posting_id,
    j.job_title,
    c.company_name,
    l.city,
    l.country,
    j.salary_min,
    j.salary_max,
    curr.currency_code,
    el.level_name as experience_level,
    et.type_name as employment_type,
    j.posted_date,
    j.remote_allowed,
    j.visa_sponsorship,
    s.source_name,
    j.extracted_skills,
    j.extracted_technologies
FROM analytics.fact_job_posting j
JOIN analytics.dim_company c ON j.company_id = c.company_id
JOIN analytics.dim_location l ON j.location_id = l.location_id
JOIN analytics.dim_source s ON j.source_id = s.source_id
LEFT JOIN analytics.dim_currency curr ON j.currency_id = curr.currency_id
LEFT JOIN analytics.dim_experience_level el ON j.experience_level_id = el.experience_level_id
LEFT JOIN analytics.dim_employment_type et ON j.employment_type_id = et.employment_type_id
WHERE j.is_active = TRUE AND j.is_duplicate = FALSE;

-- Grant permissions
GRANT ALL ON SCHEMA raw_data TO jobs_admin;
GRANT ALL ON SCHEMA analytics TO jobs_admin;
GRANT ALL ON ALL TABLES IN SCHEMA raw_data TO jobs_admin;
GRANT ALL ON ALL TABLES IN SCHEMA analytics TO jobs_admin;
GRANT ALL ON ALL SEQUENCES IN SCHEMA raw_data TO jobs_admin;
GRANT ALL ON ALL SEQUENCES IN SCHEMA analytics TO jobs_admin;
