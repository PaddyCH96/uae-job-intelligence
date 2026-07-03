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

    # Remove extra whitespace
    text = " ".join(text.split())

    # Remove special characters (keep alphanumeric and spaces)
    text = re.sub(r'[^a-z0-9\s]', '', text)

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

    # Common UAE salary patterns
    patterns = [
        # AED 10,000 - 15,000
        r'AED\s*(\d{1,3}(?:,\d{3})*)\s*-\s*(\d{1,3}(?:,\d{3})*)',
        # 10,000 - 15,000 AED
        r'(\d{1,3}(?:,\d{3})*)\s*-\s*(\d{1,3}(?:,\d{3})*)\s*AED',
        # USD 3,000 - 5,000
        r'USD\s*(\d{1,3}(?:,\d{3})*)\s*-\s*(\d{1,3}(?:,\d{3})*)',
        # $3,000 - $5,000
        r'\$(\d{1,3}(?:,\d{3})*)\s*-\s*\$(\d{1,3}(?:,\d{3})*)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            min_sal = float(match.group(1).replace(',', ''))
            max_sal = float(match.group(2).replace(',', ''))

            # Determine currency
            currency = "AED"
            if "USD" in text.upper() or "$" in text:
                currency = "USD"

            return min_sal, max_sal, currency

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
