# UAE Job Intelligence Platform - Phase 1

A minimum viable intelligence engine for collecting, normalizing, and analyzing job market data in the UAE.

## 🎯 Project Overview

This platform provides real-time insights into the UAE data and AI job market through:
- Automated job data ingestion from multiple sources
- Smart deduplication using fuzzy matching
- Normalized data storage with historical snapshots
- REST API for data access
- Interactive admin dashboard

## 🏗️ Architecture

```
┌─────────────────┐
│  Data Sources   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Ingestion     │ (Python)
│   Service       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │ (Raw + Analytics)
│   Database      │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────────┐
│  API   │ │Deduplication│
│FastAPI │ │  Engine    │
└───┬────┘ └────────────┘
    │
    ▼
┌─────────────────┐
│   Dashboard     │ (Streamlit)
│   (Admin UI)    │
└─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Setup

1. **Clone and navigate to project**
```bash
cd /Users/paddykadamuthuri/projects/UAE
```

2. **Create environment file**
```bash
cp .env.example .env
```

3. **Start all services**
```bash
docker compose up -d
```

4. **Access the platform**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:8501

## 📊 Services

### PostgreSQL Database
- **Port:** 5432
- **Schemas:** `raw_data`, `analytics`
- **Purpose:** Stores raw and normalized job data

### Ingestion Service
- Fetches job data from sources
- Validates and transforms data
- Stores in PostgreSQL

### Deduplication Engine
- Identifies duplicate job postings
- Uses fuzzy matching (85% similarity threshold)
- Marks duplicates without deletion

### FastAPI Backend
- **Port:** 8000
- RESTful API with filtering, search, aggregations
- Auto-generated OpenAPI documentation

### Streamlit Dashboard
- **Port:** 8501
- Real-time metrics and visualizations
- Job search and filtering interface

## 🔧 Development

### Run ingestion manually
```bash
docker compose run ingestion python -m src.ingestion.main
```

### Run deduplication
```bash
docker compose run ingestion python -m src.deduplication.engine
```

### Access database
```bash
docker compose exec postgres psql -U jobs_admin -d uae_jobs
```

### View logs
```bash
docker compose logs -f [service_name]
```

## 📁 Project Structure

```
UAE/
├── src/
│   ├── api/                 # FastAPI backend
│   │   ├── main.py
│   │   └── schemas.py
│   ├── dashboard/           # Streamlit UI
│   │   └── main.py
│   ├── database/            # Database models & config
│   │   ├── config.py
│   │   └── models.py
│   ├── ingestion/           # Data ingestion
│   │   ├── base.py
│   │   ├── processor.py
│   │   └── main.py
│   ├── deduplication/       # Deduplication engine
│   │   └── engine.py
│   └── utils/               # Utilities
│       ├── logger.py
│       └── text.py
├── migrations/              # Database migrations
│   └── 001_init_schema.sql
├── docs/                    # Documentation
├── tests/                   # Test files
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## 🗄️ Database Schema

### Raw Data Layer
- `raw_data.job_postings` - Raw ingested job data (JSONB)

### Analytics Layer

**Dimension Tables:**
- `dim_company` - Company information
- `dim_location` - Geographic locations
- `dim_source` - Data sources
- `dim_currency` - Currency types
- `dim_experience_level` - Experience levels
- `dim_employment_type` - Employment types
- `dim_skill` - Skills taxonomy
- `dim_technology` - Technology taxonomy

**Fact Tables:**
- `fact_job_posting` - Normalized job postings
- `fact_job_posting_snapshot` - Historical snapshots

## 🔌 API Endpoints

### Jobs
- `GET /jobs` - List jobs with filters
- `GET /jobs/{id}` - Get job by ID
- `GET /jobs/search?q={query}` - Search jobs

### Aggregations
- `GET /aggregations/by-company` - Top hiring companies
- `GET /aggregations/by-city` - Jobs by city

### Stats
- `GET /stats` - Platform statistics
- `GET /health` - Health check

## 🎯 Phase 1 Deliverables

✅ Data ingestion pipeline  
✅ Deduplication engine  
✅ PostgreSQL schema (raw + analytics)  
✅ REST API with search/filter  
✅ Admin dashboard  
✅ Docker containerization  
✅ Logging and monitoring hooks  

## 🚫 Out of Scope (Phase 1)

- LLM-based analysis
- Recommendation engines
- Advanced analytics
- User authentication
- Email alerts
- Mobile app

## 📈 Next Steps

See `Product Roadmap_ UAE AI & Data Job Intelligence Platform.md` for future phases.

## 🤝 Contributing

This is an internal project. Refer to existing documentation in markdown files for business requirements and technical specifications.

## 📝 License

Internal use only.
