-- Migration 008: User Profiles Table
-- Phase 6: Automated Job Intelligence & Career Assistant

-- Create user profiles table (opt-in only)
CREATE TABLE IF NOT EXISTS analytics.dim_user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) UNIQUE NOT NULL,
    skills JSONB DEFAULT '[]',
    experience_years INTEGER,
    expected_salary_min DECIMAL(10,2),
    expected_salary_max DECIMAL(10,2),
    preferred_cities JSONB DEFAULT '[]',
    preferred_industries JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_user ON analytics.dim_user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_skills ON analytics.dim_user_profiles USING GIN(skills);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_user_profiles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON analytics.dim_user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_user_profiles_updated_at();

-- Add comment
COMMENT ON TABLE analytics.dim_user_profiles IS 'Opt-in user profiles for personalized job recommendations (Phase 6)';
