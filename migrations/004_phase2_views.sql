-- Migration 004: Phase 2 - Analytics views for skill/technology trends
-- Creates views for trend analysis and dashboard aggregations

-- ============================================
-- 1. Technology Trends View
-- ============================================
CREATE OR REPLACE VIEW analytics.v_tech_trends AS
WITH tech_counts AS (
    SELECT
        tech AS technology_name,
        COUNT(*) AS job_count,
        MIN(fjp.posted_date) AS first_seen,
        MAX(fjp.posted_date) AS last_seen
    FROM analytics.fact_job_posting fjp,
         jsonb_array_elements_text(fjp.extracted_technologies) AS tech
    WHERE fjp.extracted_technologies IS NOT NULL
      AND fjp.is_active = TRUE
    GROUP BY tech
),
trend_calc AS (
    SELECT
        technology_name,
        job_count,
        first_seen,
        last_seen,
        CASE
            WHEN last_seen >= CURRENT_DATE - INTERVAL '30 days'
                 AND job_count >= 10 THEN 'growing'
            WHEN last_seen >= CURRENT_DATE - INTERVAL '90 days'
                 AND job_count >= 5 THEN 'established'
            WHEN last_seen < CURRENT_DATE - INTERVAL '90 days' THEN 'declining'
            ELSE 'emerging'
        END AS trend
    FROM tech_counts
)
SELECT
    technology_name,
    job_count,
    first_seen,
    last_seen,
    trend,
    CASE
        WHEN trend = 'growing' THEN '🔥'
        WHEN trend = 'established' THEN '✅'
        WHEN trend = 'declining' THEN '📉'
        ELSE '🌱'
    END AS trend_indicator
FROM trend_calc
ORDER BY job_count DESC;

-- ============================================
-- 2. Skill Trends View
-- ============================================
CREATE OR REPLACE VIEW analytics.v_skill_trends AS
WITH skill_counts AS (
    SELECT
        skill AS skill_name,
        COUNT(*) AS job_count,
        MIN(fjp.posted_date) AS first_seen,
        MAX(fjp.posted_date) AS last_seen
    FROM analytics.fact_job_posting fjp,
         jsonb_array_elements_text(fjp.extracted_skills) AS skill
    WHERE fjp.extracted_skills IS NOT NULL
      AND fjp.is_active = TRUE
    GROUP BY skill
),
trend_calc AS (
    SELECT
        skill_name,
        job_count,
        first_seen,
        last_seen,
        CASE
            WHEN last_seen >= CURRENT_DATE - INTERVAL '30 days'
                 AND job_count >= 10 THEN 'growing'
            WHEN last_seen >= CURRENT_DATE - INTERVAL '90 days'
                 AND job_count >= 5 THEN 'established'
            WHEN last_seen < CURRENT_DATE - INTERVAL '90 days' THEN 'declining'
            ELSE 'emerging'
        END AS trend
    FROM skill_counts
)
SELECT
    skill_name,
    job_count,
    first_seen,
    last_seen,
    trend,
    CASE
        WHEN trend = 'growing' THEN '🔥'
        WHEN trend = 'established' THEN '✅'
        WHEN trend = 'declining' THEN '📉'
        ELSE '🌱'
    END AS trend_indicator
FROM trend_calc
ORDER BY job_count DESC;

-- ============================================
-- 3. Salary by Skill View
-- ============================================
CREATE OR REPLACE VIEW analytics.v_salary_by_skill AS
SELECT
    skill AS skill_name,
    COUNT(*) AS job_count,
    ROUND(AVG(fjp.salary_min), 0) AS avg_salary_min,
    ROUND(AVG(fjp.salary_max), 0) AS avg_salary_max,
    ROUND(AVG((fjp.salary_min + fjp.salary_max) / 2), 0) AS avg_salary_midpoint
FROM analytics.fact_job_posting fjp,
     jsonb_array_elements_text(fjp.extracted_skills) AS skill
WHERE fjp.extracted_skills IS NOT NULL
  AND fjp.salary_min IS NOT NULL
  AND fjp.salary_max IS NOT NULL
  AND fjp.is_active = TRUE
GROUP BY skill
HAVING COUNT(*) >= 3
ORDER BY avg_salary_midpoint DESC;

-- ============================================
-- 4. Technology Co-occurrence View
-- ============================================
CREATE OR REPLACE VIEW analytics.v_tech_cooccurrence AS
SELECT
    t1 AS technology_a,
    t2 AS technology_b,
    COUNT(*) AS cooccurrence_count
FROM (
    SELECT
        fjp.job_posting_id,
        tech1.value AS t1,
        tech2.value AS t2
    FROM analytics.fact_job_posting fjp,
         jsonb_array_elements_text(fjp.extracted_technologies) AS tech1,
         jsonb_array_elements_text(fjp.extracted_technologies) AS tech2
    WHERE fjp.extracted_technologies IS NOT NULL
      AND fjp.is_active = TRUE
      AND tech1.value < tech2.value
) AS pairs
GROUP BY t1, t2
HAVING COUNT(*) >= 2
ORDER BY cooccurrence_count DESC
LIMIT 50;

-- ============================================
-- 5. Enriched Jobs Summary View
-- ============================================
CREATE OR REPLACE VIEW analytics.v_enriched_jobs AS
SELECT
    fjp.job_posting_id,
    fjp.job_title,
    fjp.job_description,
    fjp.posted_date,
    fjp.salary_min,
    fjp.salary_max,
    fjp.extracted_skills,
    fjp.extracted_technologies,
    dc.company_name,
    dl.city,
    ds.source_name,
    del.level_name AS experience_level,
    det.type_name AS employment_type
FROM analytics.fact_job_posting fjp
JOIN analytics.dim_company dc ON fjp.company_id = dc.company_id
JOIN analytics.dim_location dl ON fjp.location_id = dl.location_id
JOIN analytics.dim_source ds ON fjp.source_id = ds.source_id
LEFT JOIN analytics.dim_experience_level del ON fjp.experience_level_id = del.experience_level_id
LEFT JOIN analytics.dim_employment_type det ON fjp.employment_type_id = det.employment_type_id
WHERE fjp.is_active = TRUE;

-- ============================================
-- 6. Skill Growth Rate View (Monthly)
-- ============================================
CREATE OR REPLACE VIEW analytics.v_skill_growth AS
WITH monthly_counts AS (
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
growth_calc AS (
    SELECT
        skill_name,
        month,
        job_count,
        LAG(job_count) OVER (PARTITION BY skill_name ORDER BY month) AS prev_month_count
    FROM monthly_counts
)
SELECT
    skill_name,
    month,
    job_count,
    prev_month_count,
    CASE
        WHEN prev_month_count IS NULL OR prev_month_count = 0 THEN NULL
        ELSE ROUND(((job_count - prev_month_count)::NUMERIC / prev_month_count) * 100, 1)
    END AS growth_rate_pct
FROM growth_calc
ORDER BY skill_name, month;