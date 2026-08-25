# Context for Future AI Sessions

## Quick Summary
This is **Phase 1** of the UAE Job Intelligence Platform - a job market intelligence engine (NOT a job board) that collects and analyzes UAE data/AI job postings.

## What Exists (Complete)
✅ PostgreSQL database with star schema (12 tables)  
✅ Data ingestion pipeline with mock source  
✅ Deduplication engine (fuzzy matching)  
✅ FastAPI backend with 10+ endpoints  
✅ Streamlit admin dashboard  
✅ Full Docker Compose setup  
✅ Comprehensive documentation  

## File Structure
```
src/
├── api/          # FastAPI (main.py, schemas.py)
├── dashboard/    # Streamlit (main.py)
├── database/     # SQLAlchemy models & config
├── ingestion/    # Data collection (base.py, processor.py, main.py)
├── deduplication/# Duplicate detection (engine.py)
└── utils/        # Logging & text processing

migrations/       # SQL schema (001_init_schema.sql)
docs/            # API.md, ARCHITECTURE.md
*.md files       # README, PROJECT, BUILD, SETUP, CONTEXT
```

## Key Commands
```bash
# Start everything
docker compose up -d

# Run ingestion
docker compose run --rm ingestion python -m src.ingestion.main

# Run deduplication  
docker compose run --rm ingestion python -m src.deduplication.engine

# Access API: http://localhost:8000/docs
# Access Dashboard: http://localhost:8501
```

## Important Files to Read First
1. **PROJECT.md** - Full project context, decisions, philosophy
2. **README.md** - Quick start guide
3. **BUILD.md** - Build, deploy, troubleshoot
4. **ARCHITECTURE.md** - System design
5. Original requirements: `Product Requirements_ UAE...md`, `Data Model_ UAE...md`

## What NOT to Do
❌ Don't add LLM features yet (Phase 2)  
❌ Don't modify database schema without migration  
❌ Don't add real data sources yet (only mock for Phase 1)  
❌ Don't add authentication (Phase 2)  
❌ Don't change .env.example defaults  

## Next Session Tasks (Phase 2 Ideas)
- Add real data sources (LinkedIn API, Bayt.com scraper)
- Integrate Ollama + Qwen for skill extraction
- Add Prefect orchestration
- Implement dbt transformations
- Add pytest test suite
- Create public-facing dashboard

## Database Schema Quick Reference
**Fact:** `analytics.fact_job_posting` (main job data)  
**Dims:** company, location, source, currency, experience_level, employment_type, skill, technology  
**Raw:** `raw_data.job_postings` (JSONB)  
**View:** `analytics.v_active_jobs` (pre-joined view)

## Configuration
All config in `.env` (copy from `.env.example`)  
Key settings: POSTGRES_*, DEDUP_SIMILARITY_THRESHOLD (0.85), LOG_LEVEL

## Common Issues
- Port conflicts: Change API_PORT/DASHBOARD_PORT in .env
- DB connection: Ensure postgres is healthy (`docker compose ps`)
- Services won't start: `docker compose down -v && docker compose up -d --build`

## Code Style
- Structured logging with `structlog`
- Type hints on all functions
- Pydantic for API schemas
- SQLAlchemy ORM for database
- No hardcoded values (use env vars)

## Testing Status
⚠️ No automated tests yet (Phase 1 = manual testing)  
Tested via: curl commands, dashboard UI, direct database queries

## Dependencies
See `requirements.txt` for full list. Key ones:
- fastapi, uvicorn (API)
- streamlit, plotly (Dashboard)
- sqlalchemy, psycopg2-binary (Database)
- fuzzywuzzy (Deduplication)
- structlog (Logging)

## Git Workflow
- Main branch: `main` (production-ready)
- All work in feature branches
- Meaningful commit messages

## Last Updated
July 3, 2026 - Phase 1 Complete by AI Assistant
