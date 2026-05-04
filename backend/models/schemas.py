from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class TierEnum(str, Enum):
    S = "S"
    A = "A"
    B = "B"
    C = "C"


class SignalEnum(str, Enum):
    exit = "exit"
    hiring = "hiring"
    funding = "funding"
    growth = "growth"
    pain = "pain"
    tech = "tech"
    moat = "moat"


# ── INPUT MODELS ─────────────────────────────────────────────────────────────

class CompanyInput(BaseModel):
    company: str
    industry: str = "Unknown"
    contact_name: str = ""
    contact_title: str = ""
    email: str = ""
    employees: str = ""
    revenue_est: str = ""
    website: str = ""
    location: str = ""
    signals: List[str] = []
    description: str = ""


class BatchEnrichRequest(BaseModel):
    companies: List[CompanyInput]
    force_refresh: bool = False


# ── SCORE MODELS ─────────────────────────────────────────────────────────────

class ARSScores(BaseModel):
    ars: int = Field(..., ge=0, le=100, description="ARS Composite score")
    exit: int = Field(..., ge=0, le=100, description="Owner exit signal score")
    financial: int = Field(..., ge=0, le=100, description="Financial health proxy score")
    ops: int = Field(..., ge=0, le=100, description="Operational leverage score")
    tailwinds: int = Field(..., ge=0, le=100, description="Market tailwinds score")
    moat: int = Field(..., ge=0, le=100, description="Competitive moat score")


class AIEnrichment(BaseModel):
    ai_analysis: str
    risk_flags: Optional[str] = None
    email_draft: str
    outreach_angle: Optional[str] = None
    scored_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ── ENRICHED COMPANY ─────────────────────────────────────────────────────────

class EnrichedCompany(BaseModel):
    id: str
    company: str
    industry: str
    contact_name: str
    contact_title: str
    email: str
    employees: str
    revenue_est: str
    website: str
    location: str
    signals: List[str]
    description: str
    scores: ARSScores
    tier: TierEnum
    ai_enrichment: Optional[AIEnrichment] = None
    scraped_signals: Optional[Dict[str, Any]] = None
    cache_hit: bool = False


# ── JOB MODELS ───────────────────────────────────────────────────────────────

class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class EnrichmentJob(BaseModel):
    job_id: str
    status: JobStatus
    total: int
    completed: int
    failed: int
    results: List[EnrichedCompany] = []
    created_at: str
    updated_at: str


# ── RESPONSE MODELS ───────────────────────────────────────────────────────────

class BatchEnrichResponse(BaseModel):
    job_id: str
    status: JobStatus
    total: int
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    total: int
    completed: int
    failed: int
    progress_pct: float
    results: List[EnrichedCompany] = []


class HealthResponse(BaseModel):
    status: str
    supabase: str
    redis: str
    anthropic: str
    ai_mode: str = "heuristic"   # "heuristic" | "claude-ai"
    version: str = "1.0.0"
