-- Migration 006: Phase 4 - Predictive models, sentiment, industry classification

-- ============================================
-- 1. Add sentiment and industry columns to fact table
-- ============================================
ALTER TABLE analytics.fact_job_posting 
ADD COLUMN IF NOT EXISTS sentiment_score NUMERIC(3, 2) DEFAULT NULL;

-- ============================================
-- 2. Create industry dimension table
-- ============================================
CREATE TABLE IF NOT EXISTS analytics.dim_industry (
    industry_id SERIAL PRIMARY KEY,
    industry_name VARCHAR(100) UNIQUE NOT NULL,
    industry_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default industries
INSERT INTO analytics.dim_industry (industry_name, industry_description) 
VALUES 
    ('Technology', 'IT, software, data, AI, engineering roles'),
    ('Finance', 'Banking, insurance, financial services, accounting'),
    ('Government', 'Public sector, regulatory, policy, defense'),
    ('Education', 'Academic, training, edTech, teaching roles'),
    ('Consulting', 'Consulting, advisory, services, outsourcing'),
    ('Others', 'Other industries')
ON CONFLICT (industry_name) DO NOTHING;

-- ============================================
-- 3. Add industry_id foreign key to fact table
-- ============================================
ALTER TABLE analytics.fact_job_posting 
ADD COLUMN IF NOT EXISTS industry_id INTEGER 
REFERENCES analytics.dim_industry(industry_id) DEFAULT NULL;

-- ============================================
-- 4. Create skill forecast view
-- ============================================
CREATE OR REPLACE VIEW analytics.v_skill_forecast AS
WITH skill_stats AS (
    SELECT 
        skill AS skill_name,
        COUNT(*) AS current_demand,
        COUNT(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) AS demand_last_30d,
        COUNT(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '90 days' THEN 1 END) AS demand_last_90d
    FROM analytics.fact_job_posting,
         jsonb_array_elements_text(extracted_skills) AS skill
    WHERE extracted_skills IS NOT NULL
      AND is_active = TRUE
    GROUP BY skill
)
SELECT 
    skill_name,
    current_demand,
    demand_last_30d,
    demand_last_90d,
    CASE 
        WHEN demand_last_30d > demand_last_90d * 0.4 THEN 'growing'
        WHEN demand_last_30d < demand_last_90d * 0.2 THEN 'declining'
        ELSE 'stable'
    END AS trend,
    ROUND(demand_last_30d::numeric / NULLIF(demand_last_90d, 0) * 100, 1) AS growth_rate_pct
FROM skill_stats
WHERE current_demand >= 2
ORDER BY current_demand DESC;

-- ============================================
-- 5. Create salary prediction view
-- ============================================
CREATE OR REPLACE VIEW analytics.v_salary_prediction AS
SELECT 
    COALESCE(jsonb_array_length(extracted_skills), 0) AS skill_count,
    COALESCE(jsonb_array_length(extracted_technologies), 0) AS tech_count,
    experience_level_id,
    COUNT(*) AS sample_size,
    ROUND(AVG(salary_min), 0) AS avg_salary_min,
    ROUND(AVG(salary_max), 0) AS avg_salary_max,
    ROUND(AVG((salary_min + salary_max) / 2), 0) AS avg_salary_midpoint,
    ROUND(STDDEV((salary_min + salary_max) / 2), 0) AS salary_stddev
FROM analytics.fact_job_posting
WHERE salary_min IS NOT NULL 
  AND salary_max IS NOT NULL
  AND is_active = TRUE
GROUP BY skill_count, tech_count, experience_level_id
HAVING COUNT(*) >= 2
ORDER BY avg_salary_midpoint DESC;

-- ============================================
-- 6. Create user profile table (opt-in only)
-- ============================================
CREATE TABLE IF NOT EXISTS analytics.dim_user_profile (
    user_id UUID PRIMARY KEY,
    opt_in BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    skills_interests TEXT[] DEFAULT '{}',
    salary_expectation_min NUMERIC,
    salary_expectation_max NUMERIC
);

-- ============================================
-- 7. Create indexes for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_fact_job_posting_sentiment 
ON analytics.fact_job_posting (sentiment_score) 
WHERE sentiment_score IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_fact_job_posting_industry 
ON analytics.fact_job_posting (industry_id) 
WHERE industry_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_user_profile_optin 
ON analytics.dim_user_profile (opt_in);