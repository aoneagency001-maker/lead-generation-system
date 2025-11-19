"""
OLX Module Configuration
Настройки OLX модуля из переменных окружения
"""

from pydantic_settings import BaseSettings
from typing import Optional


class OLXSettings(BaseSettings):
    """Настройки OLX модуля"""
    
    # Supabase
    supabase_url: str
    supabase_key: str
    
    # OLX Official API
    olx_client_id: Optional[str] = None
    olx_client_secret: Optional[str] = None
    olx_api_base_url: str = "https://www.olx.kz"
    olx_oauth_url: str = "https://www.olx.kz/oauth/token/"
    
    # Module settings
    module_name: str = "olx"
    module_port: int = 8001
    module_host: str = "0.0.0.0"
    
    # Redis (для кэширования сессий)
    redis_url: str = "redis://localhost:6379/1"
    redis_session_ttl: int = 604800  # 7 дней в секундах
    
    # Playwright settings
    browser_headless: bool = True
    browser_slow_mo: int = 100  # Задержка в мс для имитации человека
    browser_timeout: int = 30000  # 30 секунд
    
    # Parser settings
    parser_rate_limit: float = 1.0  # Запросов в секунду
    parser_max_pages: int = 10
    parser_timeout: int = 60  # секунд
    
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
        env_prefix = "OLX_"
        case_sensitive = False


# Создаем глобальный экземпляр настроек
settings = OLXSettings()


