from fastapi import APIRouter
from models.schemas import HealthResponse
from core.database import get_supabase
from core.cache import get_redis
from core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="System health check")
async def health():
    settings = get_settings()

    # Check Supabase
    supabase_status = "not configured"
    if settings.supabase_url and settings.supabase_service_key:
        try:
            db = get_supabase()
            db.table("enriched_companies").select("id").limit(1).execute()
            supabase_status = "connected"
        except Exception as e:
            supabase_status = f"error: {str(e)[:50]}"

    # Check Redis
    redis_status = "not configured"
    try:
        r = await get_redis()
        if r:
            redis_status = "connected"
        else:
            redis_status = "unavailable (demo mode)"
    except Exception as e:
        redis_status = f"error: {str(e)[:50]}"

    # Check Anthropic
    anthropic_status = "not configured"
    ai_mode = "heuristic"
    if settings.anthropic_api_key:
        anthropic_status = "configured"
        ai_mode = "claude-ai"

    overall = "healthy"  # heuristic mode is fully functional

    return HealthResponse(
        status=overall,
        supabase=supabase_status,
        redis=redis_status,
        anthropic=anthropic_status,
        ai_mode=ai_mode,
    )


@router.get("/", summary="Root")
async def root():
    return {
        "name": "ARS Engine API",
        "version": "1.0.0",
        "description": "Acquisition Readiness Score — PE-grade lead intelligence",
        "docs": "/docs",
        "health": "/health",
    }
