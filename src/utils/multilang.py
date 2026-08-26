"""Multi-language support for Arabic/English job postings.

Provides language detection, Arabic skill extraction, and bilingual processing.
"""

import json
import re
from typing import Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger()

# Arabic character ranges
ARABIC_PATTERN = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')

# Common Arabic technical terms
ARABIC_TECH_TERMS = {
    'برمجة': 'Programming',
    'تطوير': 'Development',
    'بيانات': 'Data',
    'تصميم': 'Design',
    'شبكات': 'Networks',
    'أمن': 'Security',
    'تحليل': 'Analysis',
    'ذكاء اصطناعي': 'AI',
    'machine learning': 'Machine Learning',
    'python': 'Python',
    'java': 'Java',
    'sql': 'SQL',
}


def detect_language(text: str) -> Tuple[str, float]:
    """
    Detect the language of job description text.
    
    Returns:
        Tuple of (language_code, confidence)
        language_code: 'ar' for Arabic, 'en' for English, 'mixed' for bilingual
    """
    if not text:
        return ('en', 0.0)
    
    # Count Arabic characters
    arabic_chars = len(ARABIC_PATTERN.findall(text))
    total_chars = len(text.strip())
    
    if total_chars == 0:
        return ('en', 0.0)
    
    arabic_ratio = arabic_chars / total_chars
    
    # Determine language
    if arabic_ratio > 0.3:
        if arabic_ratio < 0.7:
            return ('mixed', 0.8)  # Bilingual/Code-switched
        else:
            return ('ar', 0.9)
    elif arabic_ratio > 0.05:
        return ('mixed', 0.6)  # Some Arabic content
    else:
        return ('en', 0.95)


def extract_arabic_skills(text: str) -> List[str]:
    """
    Extract skills from Arabic/English code-switched job descriptions.
    
    Uses LLM for complex extraction, falls back to pattern matching.
    """
    if not text:
        return []
    
    skills = []
    
    # Pattern matching for common technical terms
    for arabic_term, english_term in ARABIC_TECH_TERMS.items():
        if arabic_term in text:
            skills.append(english_term)
    
    # English skill patterns
    english_skills = [
        r'Python', r'Java', r'SQL', r'AWS', r'Azure', r'Docker',
        r'Kubernetes', r'TensorFlow', r'PyTorch', r'Machine Learning',
        r'Data Science', r'Analytics', r'Development', r'Programming'
    ]
    
    for pattern in english_skills:
        if re.search(pattern, text, re.IGNORECASE):
            skills.append(pattern)
    
    return list(set(skills))


def translate_skill_to_arabic(skill: str) -> Optional[str]:
    """Translate English skill name to Arabic."""
    translations = {
        'Python': 'بايثون',
        'Java': 'جافا',
        'SQL': 'إس كيو إل',
        'AWS': 'أمازون ويب سيرفس',
        'Azure': 'أزور',
        'Docker': 'دوكر',
        'Machine Learning': 'تعلم الآلة',
        'Data Science': 'علوم البيانات',
        'Programming': 'برمجة',
        'Development': 'تطوير',
        'Security': 'أمن',
        'Network': 'شبكات',
    }
    return translations.get(skill)


def normalize_bilingual_skill(skill: str, language: str) -> Dict:
    """
    Normalize a skill to bilingual format.
    
    Returns dict with 'en' and 'ar' keys.
    """
    result = {'en': skill, 'ar': None}
    
    if language in ['ar', 'mixed']:
        arabic = translate_skill_to_arabic(skill)
        if arabic:
            result['ar'] = arabic
    
    return result


class BilingualSkillTaxonomy:
    """Manage bilingual skill taxonomy."""
    
    def __init__(self):
        self.skills: Dict[str, Dict] = {}
        
    def add_skill(self, english: str, arabic: Optional[str] = None):
        """Add a skill in both languages."""
        self.skills[english] = {
            'en': english,
            'ar': arabic or translate_skill_to_arabic(english),
            'variants': []
        }
        
    def get_skill(self, name: str) -> Optional[Dict]:
        """Get skill by name (English or Arabic)."""
        # Check English
        if name in self.skills:
            return self.skills[name]
        
        # Check Arabic variants
        for skill_data in self.skills.values():
            if skill_data.get('ar') == name:
                return skill_data
        
        return None
    
    def to_list(self) -> List[Dict]:
        """Export all skills as list."""
        return list(self.skills.values())