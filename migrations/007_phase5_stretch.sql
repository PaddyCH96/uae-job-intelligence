-- Migration 007: Phase 5 - Stretch Goals (Experimental)
-- All tables/views are conditional on feature flags

-- ============================================
-- 1. Multi-Language: Language column
-- ============================================
ALTER TABLE raw_data.job_postings 
ADD COLUMN IF NOT EXISTS language VARCHAR(2) DEFAULT 'en';

-- ============================================
-- 2. Geospatial: District column
-- ============================================
ALTER TABLE raw_data.job_postings 
ADD COLUMN IF NOT EXISTS district VARCHAR(100) DEFAULT NULL;

-- ============================================
-- 3. Geospatial: District dimension table
-- ============================================
CREATE TABLE IF NOT EXISTS analytics.dim_district (
    district_id SERIAL PRIMARY KEY,
    district_name VARCHAR(100) UNIQUE NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(50) DEFAULT 'UAE',
    latitude NUMERIC(10, 6),
    longitude NUMERIC(10, 6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert UAE districts
INSERT INTO analytics.dim_district (district_name, city, latitude, longitude) VALUES
('Dubai Marina', 'Dubai', 25.0800, 55.1340),
('Downtown Dubai', 'Dubai', 25.1972, 55.2744),
('Business Bay', 'Dubai', 25.1856, 55.2644),
('DIFC', 'Dubai', 25.2131, 55.2797),
('Palm Jumeirah', 'Dubai', 25.1124, 55.1389),
('Dubai Silicon Oasis', 'Dubai', 25.1090, 55.3770),
('Abu Dhabi Island', 'Abu Dhabi', 24.4539, 54.3773),
('Al Maryah Island', 'Abu Dhabi', 24.4983, 54.3713),
('Sharjah City', 'Sharjah', 25.3463, 55.4209),
('Al Ain City', 'Al Ain', 24.1917, 55.8044)
ON CONFLICT (district_name) DO NOTHING;

-- ============================================
-- 4. Community: User shared insights table
-- ============================================
CREATE TABLE IF NOT EXISTS analytics.user_shared_insights (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    job_ids UUID[] DEFAULT '{}',
    notes TEXT DEFAULT '',
    shared BOOLEAN DEFAULT FALSE,
    shared_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 5. Community: User saved searches table
-- ============================================
CREATE TABLE IF NOT EXISTS analytics.user_saved_searches (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    search_criteria JSONB DEFAULT '{}',
    email_digest BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 6. Geospatial: District distribution view
-- ============================================
CREATE OR REPLACE VIEW analytics.v_geo_distribution AS
SELECT 
    COALESCE(dd.district_name, 'Unknown') as district,
    dl.city,
    dl.country,
    COUNT(*) as job_count,
    COUNT(CASE WHEN fjp.posted_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as jobs_last_30d,
    ROUND(AVG((fjp.salary_min + fjp.salary_max) / 2)::numeric, 0) as avg_salary,
    COUNT(DISTINCT dc.company_name) as unique_companies
FROM analytics.fact_job_posting fjp
LEFT JOIN analytics.dim_location dl ON fjp.location_id = dl.location_id
LEFT JOIN analytics.dim_company dc ON fjp.company_id = dc.company_id
LEFT JOIN analytics.dim_district dd ON dl.city = dd.city
WHERE fjp.is_active = TRUE
GROUP BY dd.district_name, dl.city, dl.country
ORDER BY job_count DESC;

-- ============================================
-- 7. Real-time: Critical data view
-- ============================================
CREATE OR REPLACE VIEW analytics.v_critical_data AS
WITH salary_trends AS (
    SELECT 
        AVG((salary_min + salary_max) / 2) as current_avg_salary,
        COUNT(*) as total_jobs,
        COUNT(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as jobs_last_7d
    FROM analytics.fact_job_posting
    WHERE salary_min IS NOT NULL
      AND posted_date >= CURRENT_DATE - INTERVAL '30 days'
),
skill_trends AS (
    SELECT 
        skill,
        COUNT(*) as demand,
        COUNT(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as recent_demand
    FROM analytics.fact_job_posting,
         jsonb_array_elements_text(extracted_skills) AS skill
    WHERE extracted_skills IS NOT NULL
      AND posted_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY skill
    ORDER BY demand DESC
    LIMIT 10
)
SELECT 
    'salary_trend' as metric_type,
    JSON_BUILD_OBJECT(
        'avg_salary', current_avg_salary,
        'total_jobs', total_jobs,
        'jobs_last_7d', jobs_last_7d
    ) as metric_value,
    NOW() as timestamp
FROM salary_trends
UNION ALL
SELECT 
    'top_skills' as metric_type,
    JSON_BUILD_OBJECT(
        'skills', JSON_AGG(JSON_BUILD_OBJECT('skill', skill, 'demand', demand, 'recent', recent_demand))
    ) as metric_value,
    NOW() as timestamp
FROM skill_trends;

-- ============================================
-- 8. Indexes for new tables
-- ============================================
CREATE INDEX IF NOT EXISTS idx_job_postings_language 
ON raw_data.job_postings (language);

CREATE INDEX IF NOT EXISTS idx_job_postings_district 
ON raw_data.job_postings (district);

CREATE INDEX IF NOT EXISTS idx_user_insights_user 
ON analytics.user_shared_insights (user_id);

CREATE INDEX IF NOT EXISTS idx_user_searches_user 
ON analytics.user_saved_searches (user_id);