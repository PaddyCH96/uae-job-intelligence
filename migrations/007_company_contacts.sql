-- Migration 007: Company Contacts Table
-- Phase 6: Automated Job Intelligence & Career Assistant

-- Create company contacts table
CREATE TABLE IF NOT EXISTS analytics.dim_company_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES analytics.dim_company(company_id) ON DELETE CASCADE,
    contact_name VARCHAR(255),
    email VARCHAR(255),
    email_confidence DECIMAL(3,2) DEFAULT 0.0,
    linkedin_url VARCHAR(500),
    position VARCHAR(255),
    source VARCHAR(50),  -- 'website', 'github', 'pattern'
    is_hiring_manager BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_company_contacts_company ON analytics.dim_company_contacts(company_id);
CREATE INDEX IF NOT EXISTS idx_company_contacts_email ON analytics.dim_company_contacts(email);
CREATE INDEX IF NOT EXISTS idx_company_contacts_source ON analytics.dim_company_contacts(source);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_company_contacts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_company_contacts_updated_at
    BEFORE UPDATE ON analytics.dim_company_contacts
    FOR EACH ROW
    EXECUTE FUNCTION update_company_contacts_updated_at();

-- Add comment
COMMENT ON TABLE analytics.dim_company_contacts IS 'Company contacts enriched from public sources for Phase 6';
