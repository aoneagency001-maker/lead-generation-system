"""
Satu Module Configuration
Настройки Satu модуля из переменных окружения
"""

from pydantic_settings import BaseSettings
from typing import Optional


class SatuSettings(BaseSettings):
    """Настройки Satu модуля"""
    
    # Supabase
    supabase_url: str
    supabase_key: str
    
    # Satu.kz Official API
    satu_api_base_url: str = "https://api.satu.kz"
    satu_web_url: str = "https://satu.kz"
    
    # Module settings
    module_name: str = "satu"
    module_port: int = 8002
    module_host: str = "0.0.0.0"
    
    # Redis (для кэширования)
    redis_url: str = "redis://localhost:6379/2"
    redis_cache_ttl: int = 3600  # 1 час
    
    # Playwright settings
    browser_headless: bool = True
    browser_slow_mo: int = 100
    browser_timeout: int = 30000
    
    # Parser settings
    parser_rate_limit: float = 1.0
    parser_max_pages: int = 10
    parser_timeout: int = 60
    
    # Anti-detect settings
    use_proxy: bool = False
    proxy_url: Optional[str] = None
    rotate_user_agent: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # CORS settings
    cors_origins: list = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    class Config:
        env_file = ".env"
        env_prefix = "SATU_"
        case_sensitive = False


# Создаем глобальный экземпляр настроек
settings = SatuSettings()


