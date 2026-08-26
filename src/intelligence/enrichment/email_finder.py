"""Email Pattern Finder - Free contact enrichment from public sources."""

import re
import httpx
from typing import Optional
from src.utils.logger import logger


class EmailPatternFinder:
    """Find company emails from public sources (free)."""
    
    async def find_emails_from_website(self, domain: str) -> list[dict]:
        """
        Scrape company website for emails.
        
        Args:
            domain: Company domain (e.g., "example.com")
            
        Returns:
            List of email dictionaries
        """
        emails = []
        
        # Check common pages
        pages = ["/contact", "/about", "/team", "/careers"]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for page in pages:
                try:
                    url = f"https://{domain}{page}"
                    response = await client.get(url, follow_redirects=True)
                    
                    if response.status_code == 200:
                        found = self._extract_emails(response.text, domain)
                        emails.extend(found)
                        
                except Exception as e:
                    logger.debug(f"Failed to scrape {domain}{page}: {e}")
                    continue
        
        # Deduplicate
        seen = set()
        unique_emails = []
        for email_data in emails:
            if email_data["email"] not in seen:
                seen.add(email_data["email"])
                unique_emails.append(email_data)
        
        return unique_emails
    
    def _extract_emails(self, html: str, domain: str) -> list[dict]:
        """Extract emails from HTML."""
        emails = []
        
        # Regex for emails
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        found_emails = re.findall(email_pattern, html)
        
        for email in found_emails:
            email_lower = email.lower()
            
            # Only company emails (not generic providers)
            if domain in email_lower:
                # Check if it's likely official
                is_official = any(prefix in email_lower for prefix in [
                    "info@", "contact@", "careers@", "hr@", "recruiting@",
                    "jobs@", "talent@", "hiring@"
                ])
                
                emails.append({
                    "email": email,
                    "confidence": 0.9 if is_official else 0.7,
                    "source": "website",
                    "is_official": is_official
                })
        
        return emails
    
    async def find_email_pattern(self, domain: str) -> Optional[str]:
        """
        Detect email pattern from known emails.
        
        Args:
            domain: Company domain
            
        Returns:
            Email pattern (e.g., "first.last", "flast", "first")
        """
        emails = await self.find_emails_from_website(domain)
        
        if not emails:
            return None
        
        # Analyze pattern
        patterns = []
        for email_data in emails:
            email = email_data["email"].split("@")[0]
            
            if "." in email:
                patterns.append("first.last")
            elif len(email) <= 2:
                patterns.append("flast")
            else:
                patterns.append("first")
        
        # Return most common pattern
        from collections import Counter
        if patterns:
            return Counter(patterns).most_common(1)[0][0]
        
        return None
    
    def generate_possible_emails(self, pattern: str, domain: str, name: str) -> list[str]:
        """
        Generate possible email addresses based on pattern.
        
        Args:
            pattern: Email pattern (e.g., "first.last")
            domain: Company domain
            name: Person's name
            
        Returns:
            List of possible email addresses
        """
        # Split name
        parts = name.lower().split()
        if len(parts) < 2:
            return []
        
        first = parts[0]
        last = parts[-1]
        
        if pattern == "first.last":
            return [f"{first}.{last}@{domain}"]
        elif pattern == "flast":
            return [f"{f}{last}@{domain}"]
        elif pattern == "first":
            return [f"{first}@{domain}"]
        else:
            return [f"{first}.{last}@{domain}"]


class GitHubEmailFinder:
    """Find company emails from public GitHub commits (free)."""
    
    def __init__(self):
        self.base_url = "https://api.github.com"
    
    async def find_company_emails(self, company_name: str) -> list[dict]:
        """
        Find emails from company's GitHub commits.
        
        Args:
            company_name: Company name to search for
            
        Returns:
            List of email dictionaries
        """
        emails = []
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Search for company repos
                response = await client.get(
                    f"{self.base_url}/search/repositories",
                    params={"q": company_name, "per_page": 3}
                )
                
                if response.status_code != 200:
                    logger.warning(f"GitHub search failed: {response.status_code}")
                    return []
                
                repos = response.json().get("items", [])
                
                for repo in repos[:2]:  # Check top 2 repos
                    # Get recent commits
                    commits_response = await client.get(
                        f"{self.base_url}/repos/{repo['full_name']}/commits",
                        params={"per_page": 10}
                    )
                    
                    if commits_response.status_code != 200:
                        continue
                    
                    commits = commits_response.json()
                    
                    for commit in commits:
                        author = commit.get("author") or {}
                        commit_data = commit.get("commit", {}).get("author", {})
                        
                        email = author.get("email") or commit_data.get("email")
                        name = author.get("login") or commit_data.get("name", "")
                        
                        if email and "@" in email:
                            emails.append({
                                "email": email,
                                "name": name,
                                "confidence": 0.6,
                                "source": "github"
                            })
            
        except Exception as e:
            logger.error(f"GitHub email search failed: {e}")
        
        return emails
