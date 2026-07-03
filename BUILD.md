# Build & Deployment Guide

## Prerequisites

- Docker Desktop 4.0+
- Docker Compose 2.0+
- Git
- 4GB RAM available
- 2GB disk space

## First-Time Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd UAE
```

### 2. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit if needed (defaults work for local development)
nano .env
```

**Key Environment Variables:**

```bash
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=uae_jobs
POSTGRES_USER=jobs_admin
POSTGRES_PASSWORD=change_me_in_production

# Application
APP_ENV=development
LOG_LEVEL=INFO
API_PORT=8000
DASHBOARD_PORT=8501

# Deduplication
DEDUP_SIMILARITY_THRESHOLD=0.85
DEDUP_BATCH_SIZE=1000
```

### 3. Build & Start Services

```bash
# Build all containers
docker compose build

# Start all services in background
docker compose up -d

# Check service status
docker compose ps
```

**Expected Output:**
```
NAME                   STATUS          PORTS
uae-jobs-postgres      Up (healthy)    0.0.0.0:5432->5432/tcp
uae-jobs-api           Up (healthy)    0.0.0.0:8000->8000/tcp
uae-jobs-dashboard     Up              0.0.0.0:8501->8501/tcp
uae-jobs-ingestion     Exit 0
uae-jobs-prefect       Up (healthy)    0.0.0.0:4200->4200/tcp
```

### 4. Initialize Database

Database migrations run automatically via PostgreSQL entrypoint.

Verify:
```bash
docker compose exec postgres psql -U jobs_admin -d uae_jobs -c "\dt analytics.*"
```

### 5. Load Sample Data

```bash
# Run initial ingestion
docker compose run --rm ingestion python -m src.ingestion.main

# Run deduplication
docker compose run --rm ingestion python -m src.deduplication.engine
```

### 6. Verify Installation

```bash
# Test API
curl http://localhost:8000/health
curl http://localhost:8000/stats

# Open dashboard
open http://localhost:8501
```

## Development Workflow

### Start Services

```bash
docker compose up -d
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f dashboard
docker compose logs -f postgres
```

### Run Ingestion Manually

```bash
docker compose run --rm ingestion python -m src.ingestion.main
```

### Run Deduplication

```bash
docker compose run --rm ingestion python -m src.deduplication.engine
```

### Access Database

```bash
# psql shell
docker compose exec postgres psql -U jobs_admin -d uae_jobs

# Run query
docker compose exec postgres psql -U jobs_admin -d uae_jobs -c "SELECT COUNT(*) FROM analytics.fact_job_posting;"
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart api
docker compose restart dashboard
```

### Stop Services

```bash
# Stop without removing containers
docker compose stop

# Stop and remove containers (keeps data)
docker compose down

# Stop and remove everything including volumes (⚠️ DESTROYS DATA)
docker compose down -v
```

## Rebuilding

### After Code Changes

```bash
# Rebuild specific service
docker compose build api
docker compose up -d api

# Rebuild all services
docker compose build
docker compose up -d
```

### After Dependency Changes

```bash
# Rebuild without cache
docker compose build --no-cache

# Force recreate containers
docker compose up -d --force-recreate
```

### After Database Schema Changes

```bash
# Stop services
docker compose down

# Remove database volume
docker volume rm uae_postgres_data

# Rebuild and start
docker compose up -d
```

## Production Deployment

### Environment Preparation

1. **Update `.env` for production:**

```bash
APP_ENV=production
POSTGRES_PASSWORD=<strong-password>
LOG_LEVEL=WARNING
```

2. **Set resource limits in `docker-compose.yml`:**

```yaml
services:
  postgres:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

3. **Enable HTTPS** (using reverse proxy like Nginx/Traefik)

### Build for Production

```bash
# Build with production tag
docker compose -f docker-compose.yml build

# Start services
docker compose -f docker-compose.yml up -d
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database health
docker compose exec postgres pg_isready -U jobs_admin

# Check all containers
docker compose ps
```

## Monitoring

### Check Logs

```bash
# Follow all logs
docker compose logs -f

# Last 100 lines
docker compose logs --tail=100

# Since timestamp
docker compose logs --since 2024-07-03T10:00:00
```

### Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df
```

### Database Performance

```bash
# Active connections
docker compose exec postgres psql -U jobs_admin -d uae_jobs -c "SELECT count(*) FROM pg_stat_activity;"

# Table sizes
docker compose exec postgres psql -U jobs_admin -d uae_jobs -c "
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname IN ('analytics', 'raw_data')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

## Backup & Restore

### Backup Database

```bash
# Dump to file
docker compose exec postgres pg_dump -U jobs_admin uae_jobs > backup_$(date +%Y%m%d).sql

# Or with docker cp
docker compose exec postgres pg_dump -U jobs_admin uae_jobs > /tmp/backup.sql
docker cp uae-jobs-postgres:/tmp/backup.sql ./backup.sql
```

### Restore Database

```bash
# Stop services
docker compose down

# Remove old data
docker volume rm uae_postgres_data

# Start only postgres
docker compose up -d postgres

# Wait for postgres to be ready
sleep 10

# Restore
cat backup.sql | docker compose exec -T postgres psql -U jobs_admin uae_jobs
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :8000
lsof -i :8501
lsof -i :5432

# Change ports in .env
API_PORT=8001
DASHBOARD_PORT=8502
```

### Container Fails to Start

```bash
# Check logs
docker compose logs <service-name>

# Inspect container
docker compose ps
docker inspect <container-id>

# Rebuild
docker compose build --no-cache <service-name>
docker compose up -d <service-name>
```

### Database Connection Issues

```bash
# Verify postgres is healthy
docker compose ps postgres

# Check connection from another container
docker compose exec api python -c "from src.database import test_connection; print(test_connection())"

# Reset database
docker compose down
docker volume rm uae_postgres_data
docker compose up -d
```

### Out of Disk Space

```bash
# Clean unused images
docker image prune -a

# Clean unused volumes
docker volume prune

# Clean everything
docker system prune -a --volumes
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build & Test

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build
        run: docker compose build
      - name: Test
        run: |
          docker compose up -d
          sleep 30
          curl -f http://localhost:8000/health
```

## Performance Tuning

### PostgreSQL

Edit `docker-compose.yml`:

```yaml
services:
  postgres:
    environment:
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --data-checksums"
    command: 
      - "postgres"
      - "-c"
      - "max_connections=200"
      - "-c"
      - "shared_buffers=256MB"
      - "-c"
      - "work_mem=16MB"
```

### API Workers

```yaml
services:
  api:
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Version Management

```bash
# Tag release
git tag -a v1.0.0 -m "Phase 1 Release"
git push origin v1.0.0

# Build with version
docker compose build --build-arg VERSION=1.0.0
```
