# Setup and Testing Guide

## Initial Setup

1. **Copy environment file**
```bash
cp .env.example .env
```

2. **Start all services**
```bash
docker compose up -d
```

3. **Wait for services to be ready** (~30 seconds)
```bash
docker compose ps
```

All services should show "Up" status.

## Testing the Platform

### 1. Verify Database
```bash
docker compose exec postgres psql -U jobs_admin -d uae_jobs -c "SELECT COUNT(*) FROM analytics.dim_company;"
```

### 2. Run Sample Ingestion
```bash
docker compose run --rm ingestion python -m src.ingestion.main
```

Expected output: "ingestion_completed" with counts

### 3. Run Deduplication
```bash
docker compose run --rm ingestion python -m src.deduplication.engine
```

### 4. Test API
```bash
curl http://localhost:8000/health
curl http://localhost:8000/stats
curl "http://localhost:8000/jobs?limit=5"
```

### 5. Access Dashboard
Open browser: http://localhost:8501

You should see:
- Platform metrics
- Top companies chart
- Top cities chart
- Job listings table

## Verify All Components

```bash
# Check logs
docker compose logs api
docker compose logs dashboard
docker compose logs postgres

# Check database tables
docker compose exec postgres psql -U jobs_admin -d uae_jobs -c "\dt analytics.*"
docker compose exec postgres psql -U jobs_admin -d uae_jobs -c "\dt raw_data.*"

# View sample data
docker compose exec postgres psql -U jobs_admin -d uae_jobs -c "SELECT * FROM analytics.v_active_jobs LIMIT 5;"
```

## Troubleshooting

### Services won't start
```bash
docker compose down -v
docker compose up -d --build
```

### Database connection errors
Check that PostgreSQL is healthy:
```bash
docker compose ps postgres
docker compose logs postgres
```

### API not responding
```bash
docker compose logs api
docker compose restart api
```

### Dashboard can't connect to API
Verify API is running:
```bash
curl http://localhost:8000/health
```

## Stop Services

```bash
docker compose down
```

To remove all data:
```bash
docker compose down -v
```
