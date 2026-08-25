# API Documentation

Base URL: `http://localhost:8000`

## Authentication
Phase 1 does not require authentication.

## Endpoints

### Health Check
```http
GET /health
```
Returns API health status.

### Get Jobs
```http
GET /jobs?skip=0&limit=100&company_name=Emirates&city=Dubai&min_salary=15000&remote_only=true&visa_sponsorship=true&posted_after=2026-01-01
```

**Query Parameters:**
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Number of results (default: 100, max: 1000)
- `company_name` (string): Filter by company name (partial match)
- `city` (string): Filter by city
- `min_salary` (float): Minimum salary threshold
- `remote_only` (bool): Show only remote jobs
- `visa_sponsorship` (bool): Show only jobs with visa sponsorship
- `posted_after` (date): Jobs posted after this date (YYYY-MM-DD)

**Response:**
```json
[
  {
    "job_posting_id": "uuid",
    "job_title": "Data Engineer",
    "job_description": "...",
    "posted_date": "2026-07-03",
    "salary_min": 15000,
    "salary_max": 25000,
    "remote_allowed": true,
    "visa_sponsorship": true,
    "extracted_skills": ["Python", "SQL"],
    "extracted_technologies": ["AWS", "Spark"]
  }
]
```

### Search Jobs
```http
GET /jobs/search?q=data+engineer&skip=0&limit=50
```

Full-text search across job titles, descriptions, and company names.

### Get Single Job
```http
GET /jobs/{job_id}
```

### Aggregations

**By Company:**
```http
GET /aggregations/by-company?limit=20
```

**By City:**
```http
GET /aggregations/by-city?limit=20
```

**Response:**
```json
[
  {"name": "Emirates Group", "count": 45},
  {"name": "ADNOC", "count": 38}
]
```

### Platform Statistics
```http
GET /stats
```

**Response:**
```json
{
  "total_jobs": 1500,
  "active_jobs": 1200,
  "duplicate_jobs": 300,
  "total_companies": 150,
  "jobs_with_salary_info": 800,
  "remote_jobs": 250,
  "visa_sponsorship_jobs": 180,
  "deduplication_rate": 20.0
}
```

## Error Responses

**404 Not Found:**
```json
{
  "detail": "Job not found"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["query", "limit"],
      "msg": "ensure this value is less than or equal to 1000",
      "type": "value_error"
    }
  ]
}
```

## Interactive Documentation
Visit `http://localhost:8000/docs` for Swagger UI.
