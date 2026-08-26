-- Migration 009: Job Recommendations Table
-- Phase 6: Automated Job Intelligence & Career Assistant

-- Create job recommendations table
CREATE TABLE IF NOT EXISTS analytics.job_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) DEFAULT 'default',
    job_posting_id UUID REFERENCES analytics.fact_job_posting(job_posting_id) ON DELETE CASCADE,
    score DECIMAL(5,4),
    rank INTEGER,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '1 day')
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_recommendations_user ON analytics.job_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_score ON analytics.job_recommendations(score DESC);
CREATE INDEX IF NOT EXISTS idx_recommendations_expires ON analytics.job_recommendations(expires_at);
CREATE INDEX IF NOT EXISTS idx_recommendations_job ON analytics.job_recommendations(job_posting_id);

-- Create index for cleanup of expired recommendations
CREATE INDEX IF NOT EXISTS idx_recommendations_expired ON analytics.job_recommendations(generated_at) 
    WHERE expires_at < CURRENT_TIMESTAMP;

-- Add comment
COMMENT ON TABLE analytics.job_recommendations IS 'Daily job recommendations with 24-hour expiration (Phase 6)';

-- Create function to cleanup expired recommendations
CREATE OR REPLACE FUNCTION cleanup_expired_recommendations()
RETURNS void AS $$
BEGIN
    DELETE FROM analytics.job_recommendations 
    WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;
