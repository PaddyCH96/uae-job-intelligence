# Fix Ollama Docker Networking

## Problem
Docker containers cannot reach Ollama running on the host machine. The LLM enrichment pipeline fails with "Ollama not available" when run inside Docker.

## Root Cause
- Ollama runs on host at `localhost:11434`
- Docker containers use `localhost` to refer to themselves, not the host
- Need `host.docker.internal` hostname to reach host services

## Solution
1. Add `extra_hosts` to docker-compose.yml services (ingestion, api) to map `host.docker.internal` to host gateway
2. Make OLLAMA_BASE configurable via environment variable in llm.py
3. Update .env to include OLLAMA_BASE_URL for Docker

## Changes
- `docker-compose.yml`: Add `extra_hosts: ["host.docker.internal:host-gateway"]` to ingestion and api services
- `src/utils/llm.py`: Read OLLAMA_BASE from environment variable with fallback to localhost
- `.env`: Add OLLAMA_BASE_URL=http://host.docker.internal:11434

## Verification
1. Rebuild and restart containers
2. Run enrichment pipeline inside Docker container
3. Verify skills/technologies are extracted
