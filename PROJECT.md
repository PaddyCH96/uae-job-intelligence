# UAE Job Intelligence Platform - Project Context

## Project Overview

**Name:** UAE Job Intelligence Platform  
**Phase:** 1 - Minimum Viable Intelligence Engine  
**Status:** Complete  
**Start Date:** July 2026  
**Technology:** Python, PostgreSQL, FastAPI, Streamlit, Docker

## What This Project Is

A **job market intelligence platform** (NOT a job board) that collects, normalizes, and analyzes job posting data from the UAE market to provide actionable insights for data & AI professionals.

## Core Philosophy

1. **Intelligence over Application** - We analyze the market, we don't facilitate applications
2. **Data Quality First** - Deduplication, normalization, and validation are critical
3. **Modular & Replaceable** - Every component can be swapped independently
4. **Open Source Stack** - No paid APIs or proprietary dependencies
5. **Local-First Development** - Everything runs via `docker compose up`

## Target Users

- Data Analysts & Engineers looking for career insights
- BI Analysts researching market trends
- AI/ML Engineers tracking technology adoption
- Job seekers optimizing their skill development
- Recruiters understanding competitive landscape

## What We Built (Phase 1)

### Core Components
1. **Data Ingestion Pipeline** - Modular source connectors
2. **PostgreSQL Database** - Star schema with raw + analytics layers
3. **Deduplication Engine** - Fuzzy matching + content fingerprinting
4. **REST API** - FastAPI with search, filters, aggregations
5. **Admin Dashboard** - Streamlit for metrics and job browsing

### Key Features
- Automatic job data collection and normalization
- Smart duplicate detection (85% similarity threshold)
- Historical snapshots for trend analysis
- Real-time analytics and visualizations
- Comprehensive filtering and search

## What We DON'T Do (Phase 1)

- ❌ Job applications or user accounts
- ❌ LLM-based analysis (coming in Phase 2)
- ❌ Recommendation engines
- ❌ Email alerts or notifications
- ❌ Mobile applications
- ❌ Real-time streaming (batch processing only)

## Data Sources

**Current:**
- Mock data generator (for testing)

**Planned (Phase 2+):**
- LinkedIn Jobs (public API)
- Bayt.com
- Indeed UAE
- Company career pages (Emirates, ADNOC, Etisalat, etc.)

## Technical Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Database | PostgreSQL 16 | Raw storage + analytics |
| Backend | FastAPI | REST API |
| Frontend | Streamlit | Admin dashboard |
| Orchestration | Docker Compose | Service management |
| Logging | Structlog | Structured logs |
| Deduplication | FuzzyWuzzy | Similarity matching |

## Data Model

**Star Schema:**
- **Fact Table:** `fact_job_posting` (normalized job data)
- **Dimensions:** company, location, source, currency, experience_level, employment_type, skill, technology
- **Raw Layer:** `raw_data.job_postings` (JSONB storage)
- **Historical:** `fact_job_posting_snapshot` (trend analysis)

## Project Structure

```
UAE/
├── src/                    # Source code
│   ├── api/               # FastAPI backend
│   ├── dashboard/         # Streamlit UI
│   ├── database/          # Models & config
│   ├── ingestion/         # Data collection
│   ├── deduplication/     # Duplicate detection
│   └── utils/             # Shared utilities
├── migrations/            # Database migrations
├── docs/                  # Documentation
├── tests/                 # Test files
├── docker-compose.yml     # Service orchestration
├── Dockerfile             # Multi-stage build
├── requirements.txt       # Python dependencies
└── README.md             # Quick start guide
```

## Future Roadmap

**Phase 2 - Intelligence Generation (Planned):**
- Ollama + Qwen/Gemma integration
- Skill extraction from job descriptions
- Salary prediction models
- Technology trend analysis
- Career path recommendations

**Phase 3 - Advanced Analytics (Planned):**
- Real-time data processing with Prefect
- DuckDB for OLAP queries
- dbt Core transformations
- Public-facing dashboard
- API rate limiting & authentication

## Development Principles

1. **No Breaking Changes** - Always migrate, never destroy
2. **Environment Variables** - Zero hardcoded config
3. **Structured Logging** - Every event is queryable
4. **Docker First** - No "works on my machine"
5. **Documentation** - Every decision is recorded

## Key Decisions & Rationale

**Why PostgreSQL over MongoDB?**
- Need for ACID transactions
- Rich querying with JSONB support
- Better for analytical workloads

**Why FastAPI over Flask?**
- Async support for scalability
- Auto-generated API documentation
- Type safety with Pydantic

**Why Streamlit over React?**
- Rapid development for internal tools
- Python-native (no context switching)
- Easy deployment

**Why Fuzzy Matching over ML?**
- Phase 1 focuses on reliability over sophistication
- Fuzzy matching is deterministic and debuggable
- ML deduplication planned for Phase 2

## Environment Variables

See `.env.example` for all configuration options.

**Critical Settings:**
- `POSTGRES_*` - Database connection
- `DEDUP_SIMILARITY_THRESHOLD` - Duplicate detection (default: 0.85)
- `LOG_LEVEL` - Logging verbosity
- `API_PORT` / `DASHBOARD_PORT` - Service ports

## Testing Strategy

**Phase 1:**
- Manual testing via dashboard
- API smoke tests with curl
- Mock data for development

**Future Phases:**
- pytest for unit tests
- Integration tests for pipelines
- Load testing for API

## Known Limitations

1. **Single Source** - Only mock data currently
2. **No Authentication** - API is open
3. **Synchronous Processing** - No background jobs yet
4. **Limited Search** - Basic SQL LIKE matching
5. **No Caching** - Direct database queries

## Success Metrics (Phase 1)

- ✅ All services start with `docker compose up`
- ✅ Database migrations run successfully
- ✅ Mock data ingests without errors
- ✅ Deduplication identifies similar jobs
- ✅ API returns data in <1 second
- ✅ Dashboard loads and displays metrics

## Repository Structure

**Main Branch:** `main` (production-ready code)
**Development:** Feature branches → PR → merge to main

## Contact & Support

This is an internal project. For questions:
- Review existing `.md` documentation files
- Check `docs/` directory for detailed guides
- Consult original requirements in root `.md` files

## Last Updated

July 3, 2026 - Phase 1 Complete
