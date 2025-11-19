"""
OLX Module - FastAPI Application
Автономное API приложение для работы с OLX.kz
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from .config import settings

# Настройка логирования
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="OLX.kz Module",
    description="Autonomous OLX integration module for Lead Generation System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# ===================================
# Health Check
# ===================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "module": "olx",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "module": "olx",
        "version": "1.0.0"
    }


# ===================================
# Exception Handlers
# ===================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.log_level == "DEBUG" else "An error occurred"
        }
    )


# ===================================
# Startup/Shutdown Events
# ===================================

@app.on_event("startup")
async def startup_event():
    """Actions on application startup"""
    logger.info(f"Starting OLX Module on {settings.module_host}:{settings.module_port}")
    logger.info(f"API Documentation: http://{settings.module_host}:{settings.module_port}/docs")
    
    # TODO: Initialize Redis connection
    # TODO: Test Supabase connection
    # TODO: Initialize Playwright if needed


@app.on_event("shutdown")
async def shutdown_event():
    """Actions on application shutdown"""
    logger.info("Shutting down OLX Module")
    
    # TODO: Close Redis connection
    # TODO: Close browser instances
    # TODO: Cleanup resources


# ===================================
# Include Routers
# ===================================

from .routes import auth, parser, ads
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(parser.router, prefix="/parser", tags=["Parser"])
app.include_router(ads.router, prefix="/ads", tags=["Ads"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.module_host,
        port=settings.module_port,
        reload=True
    )

