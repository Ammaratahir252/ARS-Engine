"""
Signal Scraper Service
Collects acquisition readiness signals from public web sources.
Gracefully degrades if APIs are unavailable.
"""
import httpx
import asyncio
import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from core.config import get_settings

TIMEOUT = httpx.Timeout(10.0, connect=5.0)

# Leadership succession keywords
EXIT_KEYWORDS = [
    "coo", "general manager", "gm position", "chief operating officer",
    "president", "retirement", "succession", "transition", "exit",
    "new leadership", "operations director", "vp operations"
]

# Growth / financial health keywords
GROWTH_KEYWORDS = [
    "expanding", "growth", "new office", "new location", "hiring",
    "record revenue", "fastest growing", "award", "partnership"
]

# Pain / distress keywords  
PAIN_KEYWORDS = [
    "layoffs", "restructuring", "struggling", "losses", "downturn",
    "challenges", "headwinds", "declining", "bankruptcy"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


async def scrape_company_signals(company: str, website: str, industry: str) -> Dict[str, Any]:
    """
    Main entry point. Runs all signal collectors in parallel.
    Returns aggregated signals dict.
    """
    signals = {
        "exit_signals": [],
        "growth_signals": [],
        "pain_signals": [],
        "leadership_signals": [],
        "hiring_signals": [],
        "founding_year": None,
        "employee_count_web": None,
        "job_postings_count": 0,
        "has_coo_posting": False,
        "has_gm_posting": False,
        "glassdoor_rating": None,
        "tech_stack": [],
        "news_snippets": [],
        "web_presence_score": 0,
        "raw_description": ""
    }

    tasks = [
        _scrape_homepage(website, signals),
        _search_web_signals(company, industry, signals),
        _check_job_postings(company, website, signals),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Score web presence
    score = 0
    if signals["founding_year"]:
        score += 10
    score += min(30, signals["job_postings_count"] * 5)
    if signals["has_coo_posting"] or signals["has_gm_posting"]:
        score += 25
    score += min(20, len(signals["growth_signals"]) * 5)
    score += min(15, len(signals["tech_stack"]) * 3)
    signals["web_presence_score"] = min(100, score)

    return signals


async def _scrape_homepage(website: str, signals: Dict) -> None:
    """Scrape company homepage for founding year, tech stack, description."""
    if not website:
        return
    url = website if website.startswith("http") else f"https://{website}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            r = await client.get(url, headers=HEADERS)
            if r.status_code != 200:
                return
            soup = BeautifulSoup(r.text, "html.parser")

            # Get meta description
            meta = soup.find("meta", {"name": "description"}) or soup.find("meta", {"property": "og:description"})
            if meta and meta.get("content"):
                signals["raw_description"] = meta["content"][:500]

            text = soup.get_text(" ", strip=True).lower()

            # Find founding year
            years = re.findall(r'\b(19[6-9]\d|200\d|201\d|202[0-3])\b', text)
            if years:
                signals["founding_year"] = int(sorted(years)[0])

            # Detect tech stack from scripts
            scripts = [s.get("src", "") for s in soup.find_all("script", src=True)]
            tech = []
            tech_map = {
                "react": "React", "vue": "Vue", "angular": "Angular",
                "shopify": "Shopify", "salesforce": "Salesforce",
                "hubspot": "HubSpot", "stripe": "Stripe",
                "wordpress": "WordPress", "wix": "Wix",
                "aws": "AWS", "cloudflare": "Cloudflare"
            }
            for src in scripts:
                for key, name in tech_map.items():
                    if key in src.lower() and name not in tech:
                        tech.append(name)
            signals["tech_stack"] = tech

            # Classify text signals
            for kw in EXIT_KEYWORDS:
                if kw in text and kw not in signals["exit_signals"]:
                    signals["exit_signals"].append(kw)
            for kw in GROWTH_KEYWORDS:
                if kw in text and kw not in signals["growth_signals"]:
                    signals["growth_signals"].append(kw)
            for kw in PAIN_KEYWORDS:
                if kw in text and kw not in signals["pain_signals"]:
                    signals["pain_signals"].append(kw)

    except Exception:
        pass  # graceful degradation


async def _search_web_signals(company: str, industry: str, signals: Dict) -> None:
    """Search for company news and signals via Brave or SerpAPI."""
    s = get_settings()
    query = f"{company} {industry} acquisition OR retirement OR CEO OR leadership 2024 OR 2025"

    if s.brave_api_key:
        await _brave_search(query, s.brave_api_key, signals)
    elif s.serpapi_key:
        await _serpapi_search(query, s.serpapi_key, signals)
    else:
        # No search API — use lightweight DuckDuckGo
        await _ddg_search(company, industry, signals)


async def _brave_search(query: str, api_key: str, signals: Dict) -> None:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": 5},
                headers={"Accept": "application/json", "X-Subscription-Token": api_key}
            )
            if r.status_code == 200:
                data = r.json()
                for result in data.get("web", {}).get("results", []):
                    snippet = result.get("description", "").lower()
                    signals["news_snippets"].append(result.get("description", "")[:200])
                    for kw in EXIT_KEYWORDS:
                        if kw in snippet and kw not in signals["exit_signals"]:
                            signals["exit_signals"].append(kw)
                    for kw in GROWTH_KEYWORDS:
                        if kw in snippet and kw not in signals["growth_signals"]:
                            signals["growth_signals"].append(kw)
    except Exception:
        pass


async def _serpapi_search(query: str, api_key: str, signals: Dict) -> None:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(
                "https://serpapi.com/search",
                params={"q": query, "api_key": api_key, "num": 5, "engine": "google"}
            )
            if r.status_code == 200:
                data = r.json()
                for result in data.get("organic_results", []):
                    snippet = result.get("snippet", "").lower()
                    signals["news_snippets"].append(result.get("snippet", "")[:200])
                    for kw in EXIT_KEYWORDS:
                        if kw in snippet and kw not in signals["exit_signals"]:
                            signals["exit_signals"].append(kw)
    except Exception:
        pass


async def _ddg_search(company: str, industry: str, signals: Dict) -> None:
    """Fallback: DuckDuckGo instant answers (no API key needed)."""
    try:
        query = f"{company} {industry}"
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1},
                headers=HEADERS
            )
            if r.status_code == 200:
                data = r.json()
                abstract = data.get("AbstractText", "").lower()
                if abstract:
                    signals["news_snippets"].append(abstract[:300])
                    for kw in EXIT_KEYWORDS:
                        if kw in abstract:
                            signals["exit_signals"].append(kw)
                    for kw in GROWTH_KEYWORDS:
                        if kw in abstract:
                            signals["growth_signals"].append(kw)
    except Exception:
        pass


async def _check_job_postings(company: str, website: str, signals: Dict) -> None:
    """Check for leadership succession job postings."""
    try:
        # Search Indeed/LinkedIn public listings via DuckDuckGo
        query = f'"{company}" hiring (COO OR "General Manager" OR "Operations Director") site:linkedin.com OR site:indeed.com'
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1},
                headers=HEADERS
            )
            if r.status_code == 200:
                data = r.json()
                related = data.get("RelatedTopics", [])
                signals["job_postings_count"] = min(10, len(related))
                text = str(data).lower()
                if "coo" in text or "chief operating" in text:
                    signals["has_coo_posting"] = True
                    signals["exit_signals"].append("coo_posting_detected")
                if "general manager" in text or " gm " in text:
                    signals["has_gm_posting"] = True
                    signals["exit_signals"].append("gm_posting_detected")
    except Exception:
        pass
