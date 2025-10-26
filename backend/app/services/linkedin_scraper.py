"""
LinkedIn Profile Scraper Service
Extracts user persona from LinkedIn profiles for chat behavior
"""
import httpx
import json
import re
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# API Configuration
BRIGHTDATA_API_KEY = "ba8aa94e5fd7d1f8d1a7c3088cbf75622103fda56729e25b3bf1db71d6922113"
BRIGHTDATA_ZONE = "web_unlocker1_linkedin"

def looks_like_profile(html: str) -> bool:
    """Check if HTML looks like a real LinkedIn profile"""
    return any([
        re.search(r'<meta property="og:title" content="[^"]+"', html, re.I),
        re.search(r'text-heading-xlarge', html, re.I),
        re.search(r'profile|pv-text-details__left-panel', html, re.I),
        re.search(r'<h1[^>]*class="[^"]*text-heading-xlarge[^"]*"', html, re.I),
    ])

async def scrape_linkedin_profile(linkedin_url: str) -> Dict[str, Any]:
    """
    Scrape LinkedIn profile and extract persona data
    Returns: Dict with full_name, location, headline, company, and ai_persona
    """
    logger.info(f"🔍 Scraping LinkedIn profile: {linkedin_url}")
    
    try:
        headers = {
            "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "url": linkedin_url,
            "zone": BRIGHTDATA_ZONE,
            "format": "raw",
            "method": "GET",
            "country": "US"
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "https://api.brightdata.com/request",
                headers=headers,
                json=payload
            )

        if response.status_code != 200:
            logger.error(f"❌ BrightData failed: {response.status_code}")
            return None

        raw = response.text
        html_content = json.loads(raw) if raw.startswith('"') else raw

        if not html_content or len(html_content) < 100:
            logger.error("❌ No HTML content received")
            return None

        if not looks_like_profile(html_content):
            logger.error("❌ LinkedIn blocked or returned gateway page")
            return None

        # Extract name
        name = extract_name(html_content, linkedin_url)
        
        # Extract headline
        headline = extract_headline(html_content)
        
        # Extract location
        location = extract_location(html_content)
        
        # Extract company
        company = extract_company(headline, html_content)
        
        # Generate simple persona description
        persona = generate_persona(name, headline, location, company)
        
        result = {
            "full_name": name,
            "headline": headline,
            "location": location,
            "company": company,
            "persona": persona
        }
        
        logger.info(f"✅ Successfully scraped profile: {name}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error scraping LinkedIn: {e}")
        return None


def extract_name(html_content: str, url: str) -> Optional[str]:
    """Extract name from HTML"""
    patterns = [
        r'<h1[^>]*class="[^"]*text-heading-xlarge[^"]*"[^>]*>([^<]+)</h1>',
        r'<h1[^>]*>([^<]+)</h1>',
        r'"name":"([^"]+)"',
        r'<title>([^|]+)\s*\|\s*LinkedIn</title>',
        r'<meta property="og:title" content="([^"]+)"',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.I)
        if match:
            return match.group(1).strip()
    
    # Fallback to URL username
    match = re.search(r'/in/([^/?#]+)', url, re.I)
    if match:
        return ' '.join(w.capitalize() for w in match.group(1).replace('-', ' ').split())
    
    return "User"


def extract_headline(html_content: str) -> Optional[str]:
    """Extract headline from HTML"""
    patterns = [
        r'"headline":"([^"]+)"',
        r'<meta property="og:description" content="([^"]+)"',
        r'class="[^"]*headline[^"]*"[^>]*>([^<]+)</',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.I)
        if match:
            text = match.group(1).strip()
            if all(bad not in text for bad in ["View", "LinkedIn", "Location:"]):
                return text
    
    return None


def extract_location(html_content: str) -> Optional[str]:
    """Extract location from HTML"""
    patterns = [
        r'"addressLocality":"([^"]+)"',
        r'"location":"([^"]+)"',
        r'San Francisco|Bay Area|New York|California|Seattle|Austin'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.I)
        if match:
            return match.group(1 if '(' in pattern else 0).strip()
    
    return None


def extract_company(headline: str, html_content: str) -> Optional[str]:
    """Extract company from headline or HTML"""
    if headline:
        # Look for "at Company" or "@ Company"
        match = re.search(r'(?:at|@)\s+([^|,\-]+)', headline, re.I)
        if match:
            return match.group(1).strip()
    
    # Look in HTML for company
    match = re.search(r'"worksFor".*?"name":"([^"]+)"', html_content, re.I)
    if match:
        return match.group(1).strip()
    
    return None


def generate_persona(name: str, headline: str, location: str, company: str) -> str:
    """Generate a simple persona description"""
    parts = []
    
    if name:
        parts.append(f"Name: {name}")
    
    if headline:
        parts.append(f"Role: {headline}")
    
    if company:
        parts.append(f"Company: {company}")
    
    if location:
        parts.append(f"Location: {location}")
    
    return " | ".join(parts) if parts else "Professional user"

