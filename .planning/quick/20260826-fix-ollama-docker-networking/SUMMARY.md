---
status: complete
---

# Fix Ollama Docker Networking - Complete

## Changes Made
1. **docker-compose.yml**: Added `extra_hosts: ["host.docker.internal:host-gateway"]` to ingestion and api services
2. **src/utils/llm.py**: Made OLLAMA_BASE configurable via `OLLAMA_BASE_URL` environment variable
3. **.env**: Added `OLLAMA_BASE_URL=http://host.docker.internal:11434`

## Verification
- Ollama connection from Docker: Working (8 models available)
- LLM skill extraction: Working (Python, SQL, AWS extracted correctly)
- Batch enrichment: 35/35 jobs enriched successfully
- Average LLM latency: ~1.3 seconds per job

## Next Steps
- Dashboard now shows enriched data with skills/technologies
- Can run real scrapers (Bayt, GulfTalent) for live data
