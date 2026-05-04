"""
ARS Engine — FastAPI Backend
Acquisition Readiness Score Intelligence Platform

Run with:
    uvicorn main:app --reload --port 8000

Docs available at:
    http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from core.config import get_settings
from routers.enrich import router as enrich_router
from routers.health import router as health_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    print("🚀 ARS Engine starting up...")
    print(f"   Environment: {settings.app_env}")
    print(f"   Anthropic:   {'✓ configured' if settings.anthropic_api_key else '✗ missing'}")
    print(f"   Supabase:    {'✓ configured' if settings.supabase_url else '✗ not configured (demo mode)'}")
    print(f"   Redis:       {settings.redis_url[:30]}...")
    yield
    print("🛑 ARS Engine shutting down...")


app = FastAPI(
    title="ARS Engine",
    description=(
        "**Acquisition Readiness Score** — PE-grade company intelligence.\n\n"
        "Transforms raw lead lists into ranked acquisition targets using:\n"
        "- 5-dimension heuristic scoring (instant)\n"
        "- Web signal scraping (async)\n"
        "- Claude AI deep analysis (async)\n\n"
        "Built for ETA searchers and lower-middle-market PE operators."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["*"] if settings.app_env == "development" else settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── ROUTES ────────────────────────────────────────────────────────────────────
app.include_router(health_router)
app.include_router(enrich_router)
