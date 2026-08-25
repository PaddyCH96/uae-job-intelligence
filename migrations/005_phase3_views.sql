-- Migration 005: Phase 3 - Skill growth rates and salary correlation views

-- ============================================
-- 1. Skill Growth Rates (YoY)
-- ============================================
CREATE OR REPLACE VIEW analytics.v_skill_growth_rates AS
WITH monthly_skill_counts AS (
    SELECT
        skill AS skill_name,
        DATE_TRUNC('month', fjp.posted_date) AS month,
        COUNT(*) AS job_count
    FROM analytics.fact_job_posting fjp,
         jsonb_array_elements_text(fjp.extracted_skills) AS skill
    WHERE fjp.extracted_skills IS NOT NULL
      AND fjp.is_active = TRUE
    GROUP BY skill, DATE_TRUNC('month', fjp.posted_date)
),
skill_with_prev AS (
    SELECT
        skill_name,
        month,
        job_count,
        LAG(job_count, 12) OVER (PARTITION BY skill_name ORDER BY month) AS job_count_12m_ago
    FROM monthly_skill_counts
)
SELECT
    skill_name,
    month,
    job_count,
    job_count_12m_ago,
    CASE
        WHEN job_count_12m_ago IS NULL OR job_count_12m_ago = 0 THEN NULL
        ELSE ROUND(((job_count - job_count_12m_ago)::NUMERIC / job_count_12m_ago) * 100, 1)
    END AS yoy_growth_pct,
    CASE
        WHEN job_count_12m_ago IS NULL OR job_count_12m_ago = 0 THEN 'new'
        WHEN job_count > job_count_12m_ago * 1.2 THEN 'growing'
        WHEN job_count < job_count_12m_ago * 0.8 THEN 'declining'
        ELSE 'stable'
    END AS trend
FROM skill_with_prev
ORDER BY skill_name, month;

-- ============================================
-- 2. Salary Correlation View
-- ============================================
CREATE OR REPLACE VIEW analytics.v_salary_correlation AS
WITH job_features AS (
    SELECT
        fjp.job_posting_id,
        fjp.salary_min,
        fjp.salary_max,
        (fjp.salary_min + fjp.salary_max) / 2 AS salary_midpoint,
        COALESCE(ARRAY_LENGTH(fjp.extracted_skills, 1), 0) AS skill_count,
        COALESCE(ARRAY_LENGTH(fjp.extracted_technologies, 1), 0) AS tech_count,
        del.level_name AS experience_level,
        det.type_name AS employment_type,
        dc.company_name,
        dl.city
    FROM analytics.fact_job_posting fjp
    LEFT JOIN analytics.dim_experience_level del ON fjp.experience_level_id = del.experience_level_id
    LEFT JOIN analytics.dim_employment_type det ON fjp.employment_type_id = det.employment_type_id
    LEFT JOIN analytics.dim_company dc ON fjp.company_id = dc.company_id
    LEFT JOIN analytics.dim_location dl ON fjp.location_id = dl.location_id
    WHERE fjp.salary_min IS NOT NULL
      AND fjp.salary_max IS NOT NULL
      AND fjp.is_active = TRUE
)
SELECT
    job_posting_id,
    salary_min,
    salary_max,
    salary_midpoint,
    skill_count,
    tech_count,
    experience_level,
    employment_type,
    company_name,
    city,
    CORR(salary_midpoint, skill_count) OVER () AS correlation_skill_salary,
    CORR(salary_midpoint, tech_count) OVER () AS correlation_tech_salary
FROM job_features;

-- ============================================
-- 3. Technology Salary Aggregation
-- ============================================
CREATE OR REPLACE VIEW analytics.v_tech_salary_avg AS
SELECT
    tech AS technology_name,
    COUNT(*) AS job_count,
    ROUND(AVG(fjp.salary_min), 0) AS avg_salary_min,
    ROUND(AVG(fjp.salary_max), 0) AS avg_salary_max,
    ROUND(AVG((fjp.salary_min + fjp.salary_max) / 2), 0) AS avg_salary_midpoint,
    ROUND(STDDEV((fjp.salary_min + fjp.salary_max) / 2), 0) AS salary_stddev
FROM analytics.fact_job_posting fjp,
     jsonb_array_elements_text(fjp.extracted_technologies) AS tech
WHERE fjp.extracted_technologies IS NOT NULL
  AND fjp.salary_min IS NOT NULL
  AND fjp.salary_max IS NOT NULL
  AND fjp.is_active = TRUE
GROUP BY tech
HAVING COUNT(*) >= 2
ORDER BY avg_salary_midpoint DESC;

-- ============================================
-- 4. Company Hiring Stats
-- ============================================
CREATE OR REPLACE VIEW analytics.v_company_hiring AS
SELECT
    dc.company_name,
    COUNT(*) AS total_jobs,
    COUNT(CASE WHEN fjp.posted_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) AS jobs_last_30d,
    COUNT(CASE WHEN fjp.posted_date >= CURRENT_DATE - INTERVAL '90 days' THEN 1 END) AS jobs_last_90d,
    ROUND(AVG(fjp.salary_min), 0) AS avg_salary_min,
    ROUND(AVG(fjp.salary_max), 0) AS avg_salary_max,
    MIN(fjp.posted_date) AS first_job_date,
    MAX(fjp.posted_date) AS last_job_date
FROM analytics.fact_job_posting fjp
JOIN analytics.dim_company dc ON fjp.company_id = dc.company_id
WHERE fjp.is_active = TRUE
GROUP BY dc.company_name
ORDER BY total_jobs DESC;

-- ============================================
-- 5. City Distribution
-- ============================================
CREATE OR REPLACE VIEW analytics.v_city_distribution AS
SELECT
    dl.city,
    dl.country,
    COUNT(*) AS total_jobs,
    COUNT(CASE WHEN fjp.posted_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) AS jobs_last_30d,
    ROUND(AVG(fjp.salary_min), 0) AS avg_salary_min,
    ROUND(AVG(fjp.salary_max), 0) AS avg_salary_max,
    COUNT(DISTINCT dc.company_name) AS unique_companies
FROM analytics.fact_job_posting fjp
JOIN analytics.dim_location dl ON fjp.location_id = dl.location_id
JOIN analytics.dim_company dc ON fjp.company_id = dc.company_id
WHERE fjp.is_active = TRUE
GROUP BY dl.city, dl.country
ORDER BY total_jobs DESC;

-- ============================================
-- 6. GIN Indexes for Performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_fact_job_posting_skills_gin 
ON analytics.fact_job_posting USING GIN (extracted_skills);

CREATE INDEX IF NOT EXISTS idx_fact_job_posting_tech_gin 
ON analytics.fact_job_posting USING GIN (extracted_technologies);

CREATE INDEX IF NOT EXISTS idx_fact_job_posting_salary 
ON analytics.fact_job_posting (salary_min, salary_max) 
WHERE salary_min IS NOT NULL AND salary_max IS NOT NULL;