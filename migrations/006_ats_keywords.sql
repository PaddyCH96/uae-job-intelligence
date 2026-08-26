-- Migration 006: ATS Keywords Table
-- Phase 6: Automated Job Intelligence & Career Assistant

-- Create ATS keywords table
CREATE TABLE IF NOT EXISTS analytics.fact_job_ats_keywords (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_posting_id UUID REFERENCES analytics.fact_job_posting(job_posting_id) ON DELETE CASCADE,
    hard_skills JSONB DEFAULT '[]',
    soft_skills JSONB DEFAULT '[]',
    action_verbs JSONB DEFAULT '[]',
    certifications JSONB DEFAULT '[]',
    industry_terms JSONB DEFAULT '[]',
    keywords_by_category JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_ats_keywords_job ON analytics.fact_job_ats_keywords(job_posting_id);
CREATE INDEX IF NOT EXISTS idx_ats_keywords_hard_skills ON analytics.fact_job_ats_keywords USING GIN(hard_skills);
CREATE INDEX IF NOT EXISTS idx_ats_keywords_soft_skills ON analytics.fact_job_ats_keywords USING GIN(soft_skills);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_ats_keywords_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_ats_keywords_updated_at
    BEFORE UPDATE ON analytics.fact_job_ats_keywords
    FOR EACH ROW
    EXECUTE FUNCTION update_ats_keywords_updated_at();

-- Add comment
COMMENT ON TABLE analytics.fact_job_ats_keywords IS 'ATS-friendly keywords extracted from job descriptions for Phase 6';
