"""
Configuration для Competitor Parser Module
Настройки парсера
"""

from pydantic_settings import BaseSettings
from typing import Optional


class CompetitorParserSettings(BaseSettings):
    """Настройки модуля парсера конкурентов"""
    
    # Parser Settings
    default_parser_type: str = "universal"
    default_rate_limit: float = 2.0
    default_timeout: int = 30
    max_concurrent_parsers: int = 3
    max_retries: int = 3
    
    # Playwright Settings
    playwright_headless: bool = True
    playwright_timeout: int = 30000  # milliseconds
    
    # User Agents
    user_agents: list = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    # Storage
    save_raw_html: bool = False
    
    # Export Settings
    export_directory: str = "exports"
    
    # Supabase (наследуем из главного settings)
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    
    class Config:
        env_prefix = "PARSER_"
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Игнорировать дополнительные поля из .env


# Глобальный экземпляр настроек
parser_settings = CompetitorParserSettings()

