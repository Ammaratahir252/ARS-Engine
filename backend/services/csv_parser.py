"""
CSV Parser Service
Handles SaaSquatch, Apollo, Hunter.io, and generic CSV formats.
"""
import csv
import io
from typing import List, Dict, Tuple
from models.schemas import CompanyInput

# Column name aliases — maps various export formats → our canonical names
COLUMN_MAP = {
    "company": ["company", "company_name", "organization", "name", "business_name"],
    "industry": ["industry", "vertical", "sector", "category"],
    "contact_name": ["contact_name", "full_name", "name", "person_name"],
    "first_name": ["first_name", "firstname"],
    "last_name": ["last_name", "lastname"],
    "contact_title": ["title", "contact_title", "job_title", "position", "role"],
    "email": ["email", "contact_email", "email_address", "work_email"],
    "employees": ["employees", "employee_count", "headcount", "team_size", "size"],
    "revenue_est": ["revenue", "revenue_est", "annual_revenue", "rev", "arr"],
    "website": ["website", "domain", "url", "web", "company_url"],
    "location": ["location", "city", "headquarters", "hq", "address"],
    "description": ["description", "about", "summary", "overview", "bio"],
}

SIGNAL_KEYWORDS = {
    "hiring": ["hiring", "growing team", "open positions", "we're hiring"],
    "funding": ["series a", "series b", "raised", "funding", "investment"],
    "growth": ["growing", "expansion", "scaling", "rapid growth"],
    "pain": ["challenge", "struggling", "problem", "issue", "difficulty"],
    "tech": ["saas", "software", "platform", "api", "cloud", "ai", "ml"],
}


def normalize_headers(headers: List[str]) -> Dict[str, str]:
    """Map raw CSV headers → canonical field names."""
    normalized = {}
    for raw in headers:
        clean = raw.strip().lower().replace(" ", "_").replace("-", "_").replace('"', '')
        for canonical, aliases in COLUMN_MAP.items():
            if clean in aliases or clean == canonical:
                normalized[canonical] = raw
                break
            # Partial match
            for alias in aliases:
                if alias in clean or clean in alias:
                    normalized[canonical] = raw
                    break
    return normalized


def infer_signals(row: Dict, description: str) -> List[str]:
    """Infer buying signals from description text."""
    signals = []
    text = description.lower()
    for signal, keywords in SIGNAL_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            signals.append(signal)
    return signals


def parse_csv(content: str) -> Tuple[List[CompanyInput], List[str]]:
    """
    Parse CSV content → list of CompanyInput objects.
    Returns (companies, errors).
    """
    companies = []
    errors = []

    try:
        # Detect delimiter
        sample = content[:2000]
        dialect = csv.Sniffer().sniff(sample, delimiters=',\t|;')
        delimiter = dialect.delimiter
    except Exception:
        delimiter = ','

    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    raw_headers = reader.fieldnames or []
    col_map = normalize_headers(list(raw_headers))

    def get_val(row: Dict, canonical: str, default: str = "") -> str:
        raw_col = col_map.get(canonical)
        if raw_col and raw_col in row:
            return (row[raw_col] or "").strip().strip('"')
        return default

    for i, row in enumerate(reader):
        try:
            # Company name is required
            company = get_val(row, "company")
            if not company:
                continue

            # Build contact name
            contact_name = get_val(row, "contact_name")
            if not contact_name:
                first = get_val(row, "first_name")
                last = get_val(row, "last_name")
                contact_name = f"{first} {last}".strip()

            description = get_val(row, "description")
            signals = infer_signals(row, description)

            lead = CompanyInput(
                company=company,
                industry=get_val(row, "industry", "Unknown"),
                contact_name=contact_name or "Unknown",
                contact_title=get_val(row, "contact_title", "Unknown"),
                email=get_val(row, "email"),
                employees=get_val(row, "employees"),
                revenue_est=get_val(row, "revenue_est"),
                website=get_val(row, "website"),
                location=get_val(row, "location"),
                signals=signals,
                description=description,
            )
            companies.append(lead)

        except Exception as e:
            errors.append(f"Row {i+2}: {str(e)}")

    return companies, errors
