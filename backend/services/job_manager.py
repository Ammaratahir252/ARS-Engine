"""
Job Manager
Handles enrichment job lifecycle.
Uses in-memory store (always works) + Supabase persistence (when configured).
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional
from models.schemas import (
    EnrichmentJob, JobStatus, EnrichedCompany,
    CompanyInput, ARSScores, AIEnrichment
)
from services.scorer import heuristic_score, ai_enrich, get_tier
from services.scraper import scrape_company_signals
from core.cache import cache_get, cache_set
from core.database import get_supabase

# In-memory job store (always available, no external deps)
_jobs: Dict[str, EnrichmentJob] = {}


def _now() -> str:
    return datetime.utcnow().isoformat()


def create_job(companies: list) -> EnrichmentJob:
    job_id = str(uuid.uuid4())
    job = EnrichmentJob(
        job_id=job_id,
        status=JobStatus.pending,
        total=len(companies),
        completed=0,
        failed=0,
        results=[],
        created_at=_now(),
        updated_at=_now(),
    )
    _jobs[job_id] = job
    return job


def get_job(job_id: str) -> Optional[EnrichmentJob]:
    return _jobs.get(job_id)


async def run_enrichment_job(
    job_id: str,
    companies: list,
    force_refresh: bool = False
) -> None:
    """
    Background task: enriches all companies in a batch job.
    Phase 1: heuristic scoring (instant)
    Phase 2: web scraping (parallel)
    Phase 3: AI scoring (sequential to respect rate limits)
    """
    job = _jobs.get(job_id)
    if not job:
        return

    job.status = JobStatus.processing
    job.updated_at = _now()

    enriched_companies = []

    for i, company_data in enumerate(companies):
        try:
            lead = CompanyInput(**company_data) if isinstance(company_data, dict) else company_data
            company_id = f"{lead.company}::{lead.website or lead.email or str(i)}"
            cache_key = f"ars:company:{company_id.lower().replace(' ', '_')}"

            # Check cache first
            if not force_refresh:
                cached = await cache_get(cache_key)
                if cached:
                    enriched = EnrichedCompany(**cached)
                    enriched.cache_hit = True
                    enriched_companies.append(enriched)
                    job.completed += 1
                    job.updated_at = _now()
                    continue

            # Phase 1: Heuristic scoring
            scores = heuristic_score(lead)
            tier = get_tier(scores.ars)

            # Phase 2: Web scraping
            scraped = {}
            try:
                scraped = await scrape_company_signals(
                    lead.company, lead.website or "", lead.industry
                )
                # Re-score with scraped signals for better accuracy
                scores = heuristic_score(lead, scraped)
                tier = get_tier(scores.ars)
            except Exception:
                pass  # scraping is best-effort

            # Phase 3: AI enrichment
            ai_data = None
            try:
                ai_data = await ai_enrich(lead, scores, scraped)
            except Exception:
                pass  # AI is best-effort

            enriched = EnrichedCompany(
                id=str(uuid.uuid4()),
                company=lead.company,
                industry=lead.industry,
                contact_name=lead.contact_name,
                contact_title=lead.contact_title,
                email=lead.email,
                employees=lead.employees,
                revenue_est=lead.revenue_est,
                website=lead.website,
                location=lead.location,
                signals=lead.signals,
                description=lead.description,
                scores=scores,
                tier=tier,
                ai_enrichment=ai_data,
                scraped_signals=scraped,
                cache_hit=False,
            )

            # Cache result
            await cache_set(cache_key, enriched.model_dump())

            # Persist to Supabase if configured
            await _persist_to_supabase(enriched)

            enriched_companies.append(enriched)
            job.completed += 1

        except Exception as e:
            job.failed += 1

        job.updated_at = _now()

        # Small delay between AI calls to avoid rate limiting
        if i < len(companies) - 1:
            await asyncio.sleep(0.3)

    # Sort by ARS descending
    enriched_companies.sort(key=lambda x: x.scores.ars, reverse=True)
    job.results = enriched_companies
    job.status = JobStatus.completed
    job.updated_at = _now()


async def _persist_to_supabase(company: EnrichedCompany) -> None:
    """Save enrichment result to Supabase. Non-blocking, best-effort."""
    try:
        db = get_supabase()
        if not db:
            return
        record = {
            "id": company.id,
            "company": company.company,
            "industry": company.industry,
            "contact_name": company.contact_name,
            "contact_title": company.contact_title,
            "email": company.email,
            "employees": company.employees,
            "revenue_est": company.revenue_est,
            "website": company.website,
            "location": company.location,
            "signals": company.signals,
            "description": company.description,
            "ars_score": company.scores.ars,
            "exit_score": company.scores.exit,
            "financial_score": company.scores.financial,
            "ops_score": company.scores.ops,
            "tailwinds_score": company.scores.tailwinds,
            "moat_score": company.scores.moat,
            "tier": company.tier.value,
            "ai_analysis": company.ai_enrichment.ai_analysis if company.ai_enrichment else None,
            "risk_flags": company.ai_enrichment.risk_flags if company.ai_enrichment else None,
            "email_draft": company.ai_enrichment.email_draft if company.ai_enrichment else None,
        }
        db.table("enriched_companies").upsert(record).execute()
    except Exception:
        pass  # Never block on DB errors
