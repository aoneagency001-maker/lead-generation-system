"""
Main FastAPI Application
Главный сервер Lead Generation System
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from core.api.config import settings, get_cors_origins
from core.api.routes import health, niches, campaigns, leads, modules, yandex_metrika, google_analytics, analytics_export, llm_pipeline
from shared.telegram_notifier import telegram_notifier

# Competitor Parser Module
try:
    from modules.competitor_parser.api import router as parser_router
    PARSER_MODULE_AVAILABLE = True
except ImportError as e:
    PARSER_MODULE_AVAILABLE = False
    print(f"⚠️  Competitor Parser module not available: {e}")

# Data Intake Module (Analytics ETL Pipeline)
try:
    from data_intake.routes import router as data_intake_router
    DATA_INTAKE_AVAILABLE = True
except ImportError as e:
    DATA_INTAKE_AVAILABLE = False
    print(f"⚠️  Data Intake module not available: {e}")

# Visitor Tracking Module
# Используем importlib для импорта из папки с дефисом
import importlib.util
import os
from pathlib import Path

visitor_tracking_module_path = Path(__file__).parent.parent.parent / "modules" / "3-lead-qualification" / "visitor_tracking" / "api" / "routes.py"

if visitor_tracking_module_path.exists():
    try:
        spec = importlib.util.spec_from_file_location("visitor_tracking_routes", visitor_tracking_module_path)
        visitor_tracking_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(visitor_tracking_module)
        visitor_tracking_router = visitor_tracking_module.router
        VISITOR_TRACKING_AVAILABLE = True
    except Exception as e:
        VISITOR_TRACKING_AVAILABLE = False
        print(f"⚠️  Visitor Tracking module not available: {e}")
else:
    VISITOR_TRACKING_AVAILABLE = False
    print(f"⚠️  Visitor Tracking module not found at: {visitor_tracking_module_path}")

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
    
    # Уведомление о старте в Telegram
    await telegram_notifier.send_success(
        message=f"🚀 Lead Generation System started!\n"
                f"Environment: {'Development' if settings.debug else 'Production'}\n"
                f"Version: 0.1.0",
        module="System"
    )
    
    yield
    
    # Shutdown
    logger.info("👋 Lead Generation System останавливается...")
    
    # Уведомление об остановке в Telegram
    await telegram_notifier.send_warning(
        message="🛑 Lead Generation System is shutting down...",
        module="System"
    )


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
app.include_router(yandex_metrika.router, prefix="/api", tags=["Yandex Metrika"])
app.include_router(google_analytics.router, prefix="/api", tags=["Google Analytics"])
app.include_router(analytics_export.router, prefix="/api", tags=["Analytics Export"])
app.include_router(llm_pipeline.router, prefix="/api", tags=["LLM Pipeline"])

# Competitor Parser Module
if PARSER_MODULE_AVAILABLE:
    app.include_router(parser_router, prefix="/api", tags=["Competitor Parser"])
    logger.info("✅ Competitor Parser module loaded")

# Visitor Tracking Module
if VISITOR_TRACKING_AVAILABLE:
    app.include_router(visitor_tracking_router, prefix="/api/visitor-tracking", tags=["Visitor Tracking"])
    logger.info("✅ Visitor Tracking module loaded")

# Data Intake Module (Analytics ETL: Raw → Normalized → Features)
if DATA_INTAKE_AVAILABLE:
    app.include_router(data_intake_router, prefix="/api", tags=["Data Intake"])
    logger.info("✅ Data Intake module loaded (3-layer analytics pipeline)")


# ============================================================================
# GLOBAL ERROR HANDLER
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Глобальный обработчик ошибок
    Ловит ВСЕ необработанные исключения и отправляет в Telegram
    """
    
    # Не отправляем HTTPException в Telegram (это ожидаемые ошибки)
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
    
    # Логируем
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        exc_info=True
    )
    
    # Отправляем в Telegram
    await telegram_notifier.send_error(
        error=exc,
        module=f"API:{request.url.path}",
        user_context={
            "method": request.method,
            "path": str(request.url.path),
            "client_ip": request.client.host if request.client else "unknown"
        },
        extra_info={
            "query_params": dict(request.query_params),
            "user_agent": request.headers.get("user-agent", "unknown")
        },
        severity="CRITICAL" if not settings.debug else "ERROR"
    )
    
    # Возвращаем generic ошибку пользователю
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Our team has been notified."
        }
    )


# ============================================================================
# ROUTES
# ============================================================================

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

