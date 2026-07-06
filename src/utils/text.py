"""Text processing and normalization utilities."""

import re
import hashlib
from typing import Optional


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison and matching.

    Args:
        text: Input text

    Returns:
        Normalized text
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Remove special characters (keep alphanumeric and spaces)
    text = re.sub(r'[^a-z0-9\s]', '', text)

    # Collapse whitespace after stripping special chars
    text = " ".join(text.split())

    return text.strip()


def clean_html(text: str) -> str:
    """
    Remove HTML tags from text.

    Args:
        text: Text potentially containing HTML

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Decode HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')

    # Remove extra whitespace
    text = " ".join(text.split())

    return text.strip()


def compute_content_hash(text: str) -> str:
    """
    Compute SHA-256 hash of text content for deduplication.

    Args:
        text: Input text

    Returns:
        64-character hex hash
    """
    if not text:
        return ""

    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def extract_salary_range(text: str) -> tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Extract salary range from text.

    Args:
        text: Text potentially containing salary information

    Returns:
        Tuple of (min_salary, max_salary, currency)
    """
    if not text:
        return None, None, None

    def _parse_num(s: str) -> float:
        return float(s.replace(',', ''))

    def _currency(t: str) -> str:
        return "USD" if ("USD" in t.upper() or "$" in t) else "AED"

    # Range patterns (with or without comma grouping)
    range_patterns = [
        r'AED\s*(\d[\d,]*)\s*-\s*(\d[\d,]*)',       # AED 10,000 - 15,000 or AED 5000 - 9000
        r'(\d[\d,]*)\s*-\s*(\d[\d,]*)\s*AED',       # 10,000 - 15,000 AED
        r'USD\s*(\d[\d,]*)\s*-\s*(\d[\d,]*)',        # USD 3,000 - 5,000
        r'\$(\d[\d,]*)\s*-\s*\$(\d[\d,]*)',          # $3,000 - $5,000
    ]

    for pattern in range_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return _parse_num(match.group(1)), _parse_num(match.group(2)), _currency(text)

    # Single-value patterns
    single_patterns = [
        r'AED\s*(\d[\d,]*)',
        r'(\d[\d,]*)\s*AED',
        r'USD\s*(\d[\d,]*)',
        r'\$(\d[\d,]*)',
    ]

    for pattern in single_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = _parse_num(match.group(1))
            return val, val, _currency(text)

    return None, None, None


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add when truncating

    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)].strip() + suffix


def extract_email(text: str) -> Optional[str]:
    """
    Extract email address from text.

    Args:
        text: Input text

    Returns:
        Email address if found, None otherwise
    """
    if not text:
        return None

    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(pattern, text)

    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    """
    Extract UAE phone number from text.

    Args:
        text: Input text

    Returns:
        Phone number if found, None otherwise
    """
    if not text:
        return None

    # UAE phone patterns
    patterns = [
        r'\+971\s?\d{1,2}\s?\d{7}',  # +971 50 1234567
        r'00971\s?\d{1,2}\s?\d{7}',  # 00971 50 1234567
        r'0\d{1,2}\s?\d{7}',  # 050 1234567
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)

    return None
