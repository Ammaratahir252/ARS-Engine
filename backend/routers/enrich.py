"""
Main API Router
All enrichment, job status, and export endpoints.
"""
import asyncio
import csv
import io
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse

from models.schemas import (
    BatchEnrichRequest, BatchEnrichResponse, JobStatusResponse,
    JobStatus, CompanyInput
)
from services.job_manager import create_job, get_job, run_enrichment_job
from services.csv_parser import parse_csv
from core.config import get_settings

router = APIRouter(prefix="/api", tags=["enrichment"])
settings = get_settings()


@router.post("/enrich", response_model=BatchEnrichResponse, summary="Submit companies for ARS enrichment")
async def enrich_batch(
    request: BatchEnrichRequest,
    background_tasks: BackgroundTasks,
):
    """
    Submit a batch of companies for ARS enrichment.
    Returns a job_id immediately. Poll /api/status/{job_id} for results.
    """
    if not request.companies:
        raise HTTPException(400, "No companies provided")

    if len(request.companies) > settings.max_batch_size:
        raise HTTPException(
            400,
            f"Batch size {len(request.companies)} exceeds max {settings.max_batch_size}. "
            "Split into smaller batches."
        )

    job = create_job(request.companies)

    # Run enrichment in background
    background_tasks.add_task(
        run_enrichment_job,
        job.job_id,
        [c.model_dump() for c in request.companies],
        request.force_refresh,
    )

    return BatchEnrichResponse(
        job_id=job.job_id,
        status=JobStatus.pending,
        total=len(request.companies),
        message=f"Job started. Poll /api/status/{job.job_id} for results.",
    )


@router.post("/enrich/csv", response_model=BatchEnrichResponse, summary="Upload CSV and enrich")
async def enrich_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    force_refresh: bool = Query(False),
):
    """Upload a CSV file (SaaSquatch/Apollo/Hunter.io format) and enrich all companies."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only CSV files are supported")

    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    companies, errors = parse_csv(text)

    if not companies:
        raise HTTPException(
            400,
            f"No valid companies found in CSV. Errors: {errors[:3]}"
        )

    if len(companies) > settings.max_batch_size:
        companies = companies[:settings.max_batch_size]

    job = create_job(companies)

    background_tasks.add_task(
        run_enrichment_job,
        job.job_id,
        [c.model_dump() for c in companies],
        force_refresh,
    )

    return BatchEnrichResponse(
        job_id=job.job_id,
        status=JobStatus.pending,
        total=len(companies),
        message=f"Parsed {len(companies)} companies from CSV. {len(errors)} rows skipped.",
    )


@router.get("/status/{job_id}", response_model=JobStatusResponse, summary="Poll job status")
async def get_job_status(job_id: str):
    """Poll enrichment job status and get partial/complete results."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")

    progress = round((job.completed + job.failed) / job.total * 100, 1) if job.total else 0

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        total=job.total,
        completed=job.completed,
        failed=job.failed,
        progress_pct=progress,
        results=job.results,
    )


@router.post("/enrich/single", summary="Enrich a single company synchronously")
async def enrich_single(company: CompanyInput):
    """
    Synchronously enrich a single company.
    Blocks until complete (~3-8 seconds). Use for single-target deep dives.
    """
    from services.scorer import heuristic_score, ai_enrich, get_tier
    from services.scraper import scrape_company_signals
    import uuid

    scores = heuristic_score(company)
    scraped = {}
    try:
        scraped = await scrape_company_signals(
            company.company, company.website or "", company.industry
        )
        scores = heuristic_score(company, scraped)
    except Exception:
        pass

    tier = get_tier(scores.ars)
    ai_data = None
    try:
        ai_data = await ai_enrich(company, scores, scraped)
    except Exception:
        pass

    from models.schemas import EnrichedCompany
    return EnrichedCompany(
        id=str(uuid.uuid4()),
        company=company.company,
        industry=company.industry,
        contact_name=company.contact_name,
        contact_title=company.contact_title,
        email=company.email,
        employees=company.employees,
        revenue_est=company.revenue_est,
        website=company.website,
        location=company.location,
        signals=company.signals,
        description=company.description,
        scores=scores,
        tier=tier,
        ai_enrichment=ai_data,
        scraped_signals=scraped,
    )


@router.get("/export/{job_id}", summary="Export scored results as CSV")
async def export_results(job_id: str):
    """Export enriched results as a scored CSV with all ARS dimensions."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    if job.status != JobStatus.completed:
        raise HTTPException(400, "Job not yet complete. Wait for status=completed.")

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Company", "Industry", "Location", "Employees", "Revenue Est.",
        "Contact Name", "Contact Title", "Email", "Website",
        "Signals", "ARS Score", "Exit Score", "Financial Score",
        "Ops Score", "Tailwinds Score", "Moat Score", "Tier",
        "AI Analysis", "Risk Flags", "Outreach Angle", "Email Draft"
    ])

    for c in job.results:
        ai = c.ai_enrichment
        writer.writerow([
            c.company, c.industry, c.location, c.employees, c.revenue_est,
            c.contact_name, c.contact_title, c.email, c.website,
            ", ".join(c.signals),
            c.scores.ars, c.scores.exit, c.scores.financial,
            c.scores.ops, c.scores.tailwinds, c.scores.moat,
            c.tier.value,
            ai.ai_analysis if ai else "",
            ai.risk_flags if ai else "",
            ai.outreach_angle if ai else "",
            ai.email_draft if ai else "",
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ars_scored_{job_id[:8]}.csv"}
    )


@router.delete("/job/{job_id}", summary="Delete a job from memory")
async def delete_job(job_id: str):
    """Clean up a completed job from memory."""
    from services.job_manager import _jobs
    if job_id not in _jobs:
        raise HTTPException(404, "Job not found")
    del _jobs[job_id]
    return {"deleted": job_id}
