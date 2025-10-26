from supabase import create_client, Client
from app.schemas.config import settings


def init_supabase() -> Client:
    """
    Initializes and returns a Supabase client using credentials from .env
    """
    url: str = settings.SUPABASE_URL
    key: str = settings.SUPABASE_KEY
    return create_client(url, key)


supabase = init_supabase()
