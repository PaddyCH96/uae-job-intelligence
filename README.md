# UAE Job Intelligence Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

A production-ready job market intelligence platform for the UAE data and AI sector. Collects, normalizes, deduplicates, and exposes job market data through a secure REST API and interactive dashboard.

## 🎯 Project Overview

This platform provides real-time insights into the UAE data and AI job market through:

- **Automated ingestion** from multiple job boards (Bayt, GulfTalent, NaukriGulf) with a mock source for development
- **Smart deduplication** using weighted fuzzy matching (85% similarity threshold) with content-hash fast-path
- **Star-schema PostgreSQL** database with raw/analytics separation, historical snapshots, and seed data
- **Secure FastAPI REST API** with input validation, rate limiting, configurable CORS, and environment-driven secrets
- **Streamlit admin dashboard** with real-time metrics, charts, and filtering
- **Docker Compose** deployment with Redis-backed distributed rate limiting

## 🏗️ Architecture

```
┌─────────────────┐
│  Data Sources   │  (Bayt, GulfTalent, NaukriGulf, Mock)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Ingestion     │  (Python, tenacity retry, robots.txt compliant)
│   Service       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │  (raw_data + analytics schemas)
│   Database      │  12 tables, indexes, triggers, views, seed data
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────────┐
│  API   │ │Deduplication│
│FastAPI │ │  Engine    │  (fuzzywuzzy, content-hash, O(n) candidate blocking)
└───┬────┘ └────────────┘
    │
    ▼
┌─────────────────┐
│   Dashboard     │  (Streamlit + Plotly)
│   (Admin UI)    │
└─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/PaddyCH96/uae-job-intelligence.git
cd uae-job-intelligence
```

2. **Create environment file**
```bash
cp .env.example .env
# Edit .env and set POSTGRES_PASSWORD (required)
# Optionally set CORS_ORIGINS, REDIS_URL, rate limit configs
```

3. **Start all services**
```bash
docker compose up -d
```

4. **Access the platform**
| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Dashboard | http://localhost:8501 |
| Redis | localhost:6379 |
| PostgreSQL | localhost:5432 |

## ⚙️ Configuration

### Required Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_PASSWORD` | **Required** - PostgreSQL password | — |
| `POSTGRES_HOST` | Database host | `postgres` |
| `POSTGRES_PORT` | Database port | `5432` |
| `POSTGRES_DB` | Database name | `uae_jobs` |
| `POSTGRES_USER` | Database user | `jobs_admin` |

### Optional Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Comma-separated allowed origins (enables credentials) | Development: `localhost:8501`, `localhost:3000` |
| `REDIS_URL` | Redis connection for rate limiting | `redis://redis:6379/0` |
| `RATE_LIMIT_DEFAULT` | Default rate limit | `100/minute` |
| `RATE_LIMIT_SEARCH` | Search endpoint limit | `30/minute` |
| `RATE_LIMIT_STATS` | Stats endpoint limit | `10/minute` |
| `APP_ENV` | Application environment | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |

## 📊 Services

| Service | Port | Description |
|---------|------|-------------|
| **PostgreSQL** | 5432 | Primary database (raw_data, analytics schemas) |
| **Redis** | 6379 | Rate limiting backend |
| **FastAPI** | 8000 | REST API with OpenAPI docs |
| **Streamlit** | 8501 | Admin dashboard |
| **Prefect** | 4200 | Orchestration server (optional) |

## 🔧 Development

### Run ingestion manually
```bash
# Mock source (development)
docker compose run --rm ingestion python -m src.ingestion.main --source mock --pages 1

# Real sources (when configured)
docker compose run --rm ingestion python -m src.ingestion.main --source bayt --pages 5
```

### Run deduplication
```bash
docker compose run --rm ingestion python -m src.deduplication.engine
```

### Access database
```bash
docker compose exec postgres psql -U jobs_admin -d uae_jobs
```

### Run tests
```bash
docker compose run --rm -v $(pwd)/tests:/app/tests -e PYTHONPATH=/app ingestion pytest -v
```

### View logs
```bash
docker compose logs -f [service_name]
```

## 📁 Project Structure

```
uae-job-intelligence/
├── src/
│   ├── api/                 # FastAPI backend
│   │   ├── main.py          # Endpoints, CORS, rate limiting, validation
│   │   └── schemas.py       # Pydantic request/response models
│   ├── dashboard/           # Streamlit UI
│   │   └── main.py
│   ├── database/            # Database models & config
│   │   ├── config.py        # Settings, engine, sessions
│   │   └── models.py        # 12 SQLAlchemy models
│   ├── ingestion/           # Data ingestion pipeline
│   │   ├── base.py          # BaseSource ABC + MockSource
│   │   ├── processor.py     # Normalization & storage
│   │   ├── main.py          # CLI orchestration
│   │   ├── flows.py         # Prefect flows
│   │   └── sources/         # Bayt, GulfTalent, NaukriGulf scrapers
│   ├── deduplication/       # Deduplication engine
│   │   └── engine.py        # Fuzzy matching + content-hash
│   └── utils/               # Utilities
│       ├── logger.py        # Structured logging (structlog)
│       └── text.py          # Text processing, salary extraction
├── migrations/              # Database migrations
│   └── 001_init_schema.sql  # Full schema + seeds
├── alembic/                 # Alembic migration config
├── docs/                    # Documentation
├── tests/                   # Test suite (156 tests)
│   ├── test_security.py     # Security regression tests
│   ├── test_api.py
│   ├── test_deduplication.py
│   ├── test_ingestion.py
│   ├── test_flows.py
│   ├── test_sources.py
│   ├── test_text_utils.py
│   ├── test_migration_schema.py
│   ├── test_integration_pipeline.py
│   └── conftest.py          # DB fixtures, env config
├── docker-compose.yml       # 5-service stack
├── Dockerfile               # Multi-stage (ingestion, api, dashboard)
├── requirements.txt         # 48 dependencies
├── .env.example             # Environment template
└── README.md
```

## 🗄️ Database Schema

### Raw Data Layer (`raw_data` schema)
- `job_postings` - Raw ingested job data (JSONB, GIN indexed)

### Analytics Layer (`analytics` schema)

**Dimension Tables (8):**
- `dim_company` - Company information (normalized names)
- `dim_location` - Geographic locations (7 UAE cities seeded)
- `dim_source` - Data sources
- `dim_currency` - Currency types (4 seeded)
- `dim_experience_level` - Experience levels (7 seeded)
- `dim_employment_type` - Employment types (6 seeded)
- `dim_skill` - Skills taxonomy
- `dim_technology` - Technology taxonomy

**Fact Tables (2):**
- `fact_job_posting` - Normalized job postings (indexed on company, location, date, hash)
- `fact_job_posting_snapshot` - Historical daily snapshots

**Views & Constraints:**
- `v_active_jobs` - Pre-joined active non-duplicate jobs
- `check_duplicate_reference` - Enforces duplicate integrity
- `updated_at` triggers on all tables

## 🔌 API Endpoints

### Jobs
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/jobs` | GET | List jobs with filters (pagination, company, city, salary, remote, visa, date) |
| `/jobs/{id}` | GET | Get job by UUID (validated) |
| `/jobs/search?q={query}` | GET | Full-text search (2-200 chars) |

### Aggregations
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/aggregations/by-company` | GET | Top hiring companies (limit 1-100) |
| `/aggregations/by-city` | GET | Jobs by city (limit 1-100) |

### Stats & Health
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stats` | GET | Platform statistics (rate limited: 10/min) |
| `/health` | GET | Health check (rate limited: 100/min) |

### Security Features
- **CORS**: Configurable via `CORS_ORIGINS`; credentials only with explicit origins
- **Input Validation**: All params bounded (pagination 1-1000, search 2-200 chars, salary 0-1M, dates 2020-2030)
- **Rate Limiting**: Redis-backed (default 100/min, search 30/min, stats 10/min)
- **Parameterized Queries**: All SQL via SQLAlchemy ORM
- **Secrets**: No hardcoded defaults; `POSTGRES_PASSWORD` required

## 📈 Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| **Phase 1** | MVP: Ingestion, dedup, API, dashboard, Docker | ✅ Complete |
| **Phase 2** | LLM skill extraction, trend analysis, AI insights | 🔄 Planned |
| **Phase 3** | Predictive models, user profiles, recommendations | 📅 Future |

See `Product Roadmap_ UAE AI & Data Job Intelligence Platform.md` for details.

## 🧪 Testing

- **156 tests** total (97 pass, 9 pre-existing failures, 30 skipped, 20 security tests)
- **Security tests**: CORS, input validation, secrets, rate limiting, SQL injection, Docker
- **Coverage**: 58% overall (core modules 97%+)
- **Run**: `docker compose run --rm -v $(pwd)/tests:/app/tests -e PYTHONPATH=/app ingestion pytest -v`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 UAE Job Intelligence Platform

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Streamlit](https://streamlit.io/) - Rapid dashboard development
- [PostgreSQL](https://www.postgresql.org/) - Advanced open-source database
- [Redis](https://redis.io/) - In-memory data structure store
- [fuzzywuzzy](https://github.com/seatgeek/fuzzywuzzy) - Fuzzy string matching
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL toolkit