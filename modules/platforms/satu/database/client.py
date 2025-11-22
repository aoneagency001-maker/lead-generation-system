"""
Satu Module - Supabase Client
Клиент для работы с Supabase БД
"""

from supabase import create_client, Client
from functools import lru_cache
from ..api.config import settings


@lru_cache()
def get_supabase_client() -> Client:
    """
    Получить Supabase клиент (singleton)
    
    Returns:
        Client: Supabase клиент
    """
    return create_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_key
    )


async def get_db():
    """
    Dependency для FastAPI
    
    Yields:
        Client: Supabase клиент
    """
    yield get_supabase_client()



