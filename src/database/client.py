from supabase import create_client, Client
from config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)

_client: Client | None = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            logger.warning("Supabase credentials not configured, using mock mode")
            return None
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("Supabase client initialized")
    return _client
