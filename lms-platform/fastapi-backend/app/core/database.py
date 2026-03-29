from supabase import create_client, Client
from app.core.config import settings

def get_supabase_client() -> Client:
    url: str = settings.SUPABASE_URL
    key: str = settings.SUPABASE_KEY
    supabase: Client = create_client(url, key)
    return supabase

# Create a singleton instance
supabase_client = get_supabase_client()
