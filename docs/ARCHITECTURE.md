# Architecture Overview - Phase 1

## System Design Principles

1. **Modular Architecture** - Each service is independently replaceable
2. **Single Responsibility** - Each module has one clear purpose
3. **Environment-based Config** - All configuration via environment variables
4. **Docker-first** - All services containerized from day one
5. **Logging & Monitoring** - Structured logging throughout

## Data Flow

```
[Job Sources] → [Ingestion] → [Raw Storage] → [Processing] → [Analytics Storage]
                                                    ↓
                                              [Deduplication]
                                                    ↓
                                            [API] → [Dashboard]
```

## Service Architecture

### 1. PostgreSQL Database
- **Schemas:** `raw_data`, `analytics`
- **Purpose:** Single source of truth
- **Storage:** Raw JSONB + normalized star schema

### 2. Ingestion Service
- **Components:**
  - `BaseSource` - Abstract source connector
  - `MockSource` - Test data generator
  - `JobProcessor` - Normalization engine
- **Output:** Raw jobs in PostgreSQL

### 3. Deduplication Engine
- **Algorithm:** Fuzzy matching + content hashing
- **Threshold:** 85% similarity
- **Approach:** Mark duplicates, never delete

### 4. FastAPI Backend
- **Framework:** FastAPI (async)
- **Features:** Auto-docs, filtering, search, aggregations
- **Port:** 8000

### 5. Streamlit Dashboard
- **Purpose:** Admin interface
- **Features:** Metrics, charts, job browser
- **Port:** 8501

## Database Design

**Star Schema:**
- **Fact:** `fact_job_posting` (center)
- **Dimensions:** company, location, source, currency, experience, employment type

**Design Decisions:**
- UUID primary keys for distributed systems
- JSONB for flexible extracted data (skills, technologies)
- Content hash for deduplication
- Soft deletes (is_active flag)
- Historical snapshots table for trend analysis

## Technology Choices

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Database | PostgreSQL 16 | JSONB support, reliability, open-source |
| Backend | FastAPI | Modern, async, auto-docs, type safety |
| Dashboard | Streamlit | Rapid development, Python-native |
| Deduplication | FuzzyWuzzy | Battle-tested fuzzy matching |
| Logging | Structlog | Structured, queryable logs |
| Containerization | Docker Compose | Simple orchestration, reproducible environments |

## Scalability Considerations

### Phase 1 (Current)
- Single PostgreSQL instance
- Synchronous ingestion
- In-memory deduplication

### Future Phases
- Read replicas for analytics
- Async job queue (Celery/Prefect)
- DuckDB for OLAP queries
- Horizontal API scaling
