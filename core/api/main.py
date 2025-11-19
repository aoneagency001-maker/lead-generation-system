"""
Main FastAPI Application
Главный сервер Lead Generation System
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from core.api.config import settings, get_cors_origins
from core.api.routes import health, niches, campaigns, leads, modules

# Competitor Parser Module
try:
    from modules.competitor_parser.api import router as parser_router
    PARSER_MODULE_AVAILABLE = True
except ImportError as e:
    PARSER_MODULE_AVAILABLE = False
    print(f"⚠️  Competitor Parser module not available: {e}")

# Настройка логирования
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    # Startup
    logger.info("🚀 Lead Generation System запускается...")
    logger.info(f"📊 Supabase URL: {settings.supabase_url}")
    logger.info(f"🤖 Debug режим: {settings.debug}")
    
    yield
    
    # Shutdown
    logger.info("👋 Lead Generation System останавливается...")


# Создаем FastAPI приложение
app = FastAPI(
    title="Lead Generation System",
    description="Модульная система автоматизации лид-генерации",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(niches.router, prefix="/api/niches", tags=["Niches"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(leads.router, prefix="/api/leads", tags=["Leads"])
app.include_router(modules.router, prefix="/api", tags=["Modules"])

# Competitor Parser Module
if PARSER_MODULE_AVAILABLE:
    app.include_router(parser_router, prefix="/api", tags=["Competitor Parser"])
    logger.info("✅ Competitor Parser module loaded")


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Lead Generation System API",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "core.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )

