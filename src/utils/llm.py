"""LLM integration for skill/technology extraction via Ollama.

Uses qwen2.5-coder:7b for extracting skills and technologies from job descriptions.
Falls back to fuzzy matching if LLM is unavailable.
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List, Optional

import requests

from src.utils.logger import logger

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = "qwen2.5-coder:7b"

# Prompt templates for extraction
SKILL_EXTRACTION_PROMPT = """Extract the technical skills and tools mentioned in this job description.
Return ONLY a JSON array of skill names. No prose, no explanations.
Return exactly this format: ["skill1", "skill2", ...]

Job Description:
{description}

Skills (JSON array):"""

TECHNOLOGY_EXTRACTION_PROMPT = """Extract the technologies, platforms, and cloud services mentioned in this job description.
Return ONLY a JSON array of technology names. No prose, no explanations.
Return exactly this format: ["tech1", "tech2", ...]

Job Description:
{description}

Technologies (JSON array):"""

SENTIMENT_PROMPT = """Analyze the job description below and return a JSON with:
- "sentiment_score": number between -1 (very negative) and 1 (very positive)
- "sentiment_label": "positive" | "negative" | "neutral"
- "factors": array of 1-3 strings explaining the sentiment

Job Description:
{description}

Return ONLY valid JSON, no prose."""

INDUSTRY_PROMPT = """Classify this job into exactly ONE of these industries:
- Technology: IT, software, data, AI, engineering roles
- Finance: Banking, insurance, financial services, accounting
- Government: Public sector, regulatory, policy, defense
- Education: Academic, training, edTech, teaching roles
- Consulting: Consulting, advisory, services, outsourcing
- Others: Everything else

Job Description:
{description}

Return ONLY the industry name, no prose, no explanations."""


# ---------------------------------------------------------------------------
# LLM Functions
# ---------------------------------------------------------------------------

def extract_with_llm(
    prompt: str,
    model: str = DEFAULT_MODEL,
    timeout: int = 30,
) -> str:
    """Send a prompt to Ollama and return the response.

    Args:
        prompt: The prompt to send to the LLM
        model: Ollama model name (default: qwen2.5-coder:7b)
        timeout: Request timeout in seconds

    Returns:
        LLM response as string, or empty string on error
    """
    try:
        resp = requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        resp.raise_for_status()
        result = resp.json()
        response_text = result.get("response", "").strip()

        logger.debug(
            "llm_request_complete",
            model=model,
            response_length=len(response_text),
        )
        return response_text

    except requests.Timeout:
        logger.error("llm_timeout", model=model, timeout=timeout)
        return ""
    except requests.ConnectionError:
        logger.error("llm_connection_error", ollama_url=OLLAMA_BASE)
        return ""
    except Exception as e:
        logger.error("llm_request_failed", error=str(e))
        return ""


def parse_json_array(text: str) -> List[str]:
    """Parse a JSON array from LLM response text.

    Handles various formats the LLM might return:
    - Clean JSON: ["Python", "SQL"]
    - Text-wrapped JSON: Here are the skills: ["Python", "SQL"]
    - Markdown code block: ```json\n["Python", "SQL"]\n```

    Returns:
        List of strings, or empty list on failure
    """
    if not text:
        return []

    # Try to extract JSON array from markdown code blocks
    code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if code_block_match:
        text = code_block_match.group(1).strip()

    # Try direct JSON parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if item]
    except json.JSONDecodeError:
        pass

    # Try to find JSON array in text
    array_match = re.search(r"\[.*?\]", text, re.DOTALL)
    if array_match:
        try:
            parsed = json.loads(array_match.group())
            if isinstance(parsed, list):
                return [str(item) for item in parsed if item]
        except json.JSONDecodeError:
            pass

    # Last resort: split by comma and clean
    items = [item.strip().strip('"').strip("'") for item in text.split(",")]
    items = [item for item in items if item and len(item) > 1]
    return items


def parse_json_object(text: str) -> Dict[str, Any]:
    """Parse a JSON object from LLM response text.

    Returns:
        Dictionary, or empty dict on failure
    """
    if not text:
        return {}

    # Try to extract JSON from markdown code blocks
    code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if code_block_match:
        text = code_block_match.group(1).strip()

    # Try direct JSON parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in text
    obj_match = re.search(r"\{.*?\}", text, re.DOTALL)
    if obj_match:
        try:
            parsed = json.loads(obj_match.group())
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    return {}


# ---------------------------------------------------------------------------
# Extraction Functions
# ---------------------------------------------------------------------------

def extract_skills(description: str, model: str = DEFAULT_MODEL) -> List[str]:
    """Extract skills from a job description using LLM.

    Args:
        description: Job description text
        model: Ollama model to use

    Returns:
        List of extracted skill names
    """
    if not description:
        return []

    prompt = SKILL_EXTRACTION_PROMPT.format(description=description[:1000])
    response = extract_with_llm(prompt, model=model)
    skills = parse_json_array(response)

    logger.debug("skills_extracted", count=len(skills), skills=skills[:5])
    return skills


def extract_technologies(description: str, model: str = DEFAULT_MODEL) -> List[str]:
    """Extract technologies from a job description using LLM.

    Args:
        description: Job description text
        model: Ollama model to use

    Returns:
        List of extracted technology names
    """
    if not description:
        return []

    prompt = TECHNOLOGY_EXTRACTION_PROMPT.format(description=description[:1000])
    response = extract_with_llm(prompt, model=model)
    technologies = parse_json_array(response)

    logger.debug("technologies_extracted", count=len(technologies), technologies=technologies[:5])
    return technologies


def extract_sentiment(description: str, model: str = DEFAULT_MODEL) -> Dict[str, Any]:
    """Analyze sentiment of a job description using LLM.

    Args:
        description: Job description text
        model: Ollama model to use

    Returns:
        Dict with sentiment_score, sentiment_label, and factors
    """
    if not description:
        return {"sentiment_score": 0.0, "sentiment_label": "neutral", "factors": []}

    prompt = SENTIMENT_PROMPT.format(description=description[:1000])
    response = extract_with_llm(prompt, model=model)
    result = parse_json_object(response)

    # Ensure required fields
    result.setdefault("sentiment_score", 0.0)
    result.setdefault("sentiment_label", "neutral")
    result.setdefault("factors", [])

    logger.debug("sentiment_extracted", result=result)
    return result


def classify_industry(description: str, model: str = DEFAULT_MODEL) -> str:
    """Classify job industry using LLM.

    Args:
        description: Job description text
        model: Ollama model to use

    Returns:
        Industry name string
    """
    if not description:
        return "Others"

    prompt = INDUSTRY_PROMPT.format(description=description[:1000])
    response = extract_with_llm(prompt, model=model)

    # Clean the response
    industry = response.strip().strip('"').strip("'")

    # Validate against known industries
    valid_industries = ["Technology", "Finance", "Government", "Education", "Consulting", "Others"]
    if industry in valid_industries:
        return industry
    # Fuzzy match
    for valid in valid_industries:
        if valid.lower() in industry.lower():
            return valid

    return "Others"


# ---------------------------------------------------------------------------
# Batch Processing
# ---------------------------------------------------------------------------

def batch_extract_skills(
    descriptions: List[str],
    model: str = DEFAULT_MODEL,
    batch_size: int = 5,
    delay: float = 1.0,
) -> List[List[str]]:
    """Extract skills from multiple job descriptions in batches.

    Args:
        descriptions: List of job description texts
        model: Ollama model to use
        batch_size: Number of jobs per LLM request (not used in current implementation)
        delay: Delay between requests in seconds

    Returns:
        List of skill lists (one per description)
    """
    results = []
    for i, desc in enumerate(descriptions):
        skills = extract_skills(desc, model=model)
        results.append(skills)
        if i < len(descriptions) - 1:
            time.sleep(delay)  # Rate limiting

    return results


def batch_extract_technologies(
    descriptions: List[str],
    model: str = DEFAULT_MODEL,
    batch_size: int = 5,
    delay: float = 1.0,
) -> List[List[str]]:
    """Extract technologies from multiple job descriptions in batches.

    Args:
        descriptions: List of job description texts
        model: Ollama model to use
        batch_size: Number of jobs per LLM request (not used in current implementation)
        delay: Delay between requests in seconds

    Returns:
        List of technology lists (one per description)
    """
    results = []
    for i, desc in enumerate(descriptions):
        techs = extract_technologies(desc, model=model)
        results.append(techs)
        if i < len(descriptions) - 1:
            time.sleep(delay)  # Rate limiting

    return results


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

def check_ollama_health() -> bool:
    """Check if Ollama is running and accessible.

    Returns:
        True if Ollama is healthy, False otherwise
    """
    try:
        resp = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        resp.raise_for_status()
        return True
    except Exception:
        return False


def get_available_models() -> List[str]:
    """Get list of available Ollama models.

    Returns:
        List of model names
    """
    try:
        resp = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        return []