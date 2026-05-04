from core.config import get_settings
from functools import lru_cache

try:
    from supabase import create_client, Client
    _supabase_available = True
except ImportError:
    _supabase_available = False


@lru_cache()
def get_supabase():
    """Returns Supabase client if configured, None in demo mode."""
    if not _supabase_available:
        return None
    s = get_settings()
    if not s.supabase_url or not s.supabase_service_key:
        return None
    return create_client(s.supabase_url, s.supabase_service_key)