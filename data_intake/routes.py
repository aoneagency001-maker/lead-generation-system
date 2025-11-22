"""
Data Intake API Routes

FastAPI router for data intake endpoints.
Provides HTTP interface for fetching analytics data.

Integration with main app:
    from data_intake.routes import router as data_intake_router
    app.include_router(data_intake_router)
"""

import logging
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from data_intake.models import (
    PipelineStatus,
    SessionFeatures,
    SourceType,
    VisitEvent,
    VisitsResponse,
)
from data_intake.providers.base import (
    ProviderAPIError,
    ProviderAuthError,
    ProviderConfigError,
    ProviderError,
)
from data_intake.service import DataIntakeService, get_data_intake_service
from data_intake.pipeline import DataIntakePipeline, get_pipeline
from data_intake.database.storage import DataIntakeStorage, get_storage, StorageError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-intake", tags=["Data Intake"])


# Response models

class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    sources: dict[str, bool]
    timestamp: datetime


class SourcesListResponse(BaseModel):
    """List of available sources response."""
    sources: list[str]
    count: int


class ErrorDetail(BaseModel):
    """Error response detail."""
    error: str
    detail: Optional[str] = None
    source: Optional[str] = None


class PipelineRunRequest(BaseModel):
    """Request to run ETL pipeline."""
    source: str = Field(..., description="Source type (e.g., YANDEX_METRIKA)")
    date_from: str = Field(..., description="Start date YYYY-MM-DD")
    date_to: str = Field(..., description="End date YYYY-MM-DD")


class FeaturesResponse(BaseModel):
    """Response with features from Feature Store."""
    source: Optional[str]
    date_from: Optional[str]
    date_to: Optional[str]
    count: int
    items: list[dict]


class HotLeadsResponse(BaseModel):
    """Response with hot leads from Feature Store."""
    min_score: int
    count: int
    items: list[dict]


# Helper functions

def parse_date(date_str: str, param_name: str) -> date:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format for {param_name}. Expected YYYY-MM-DD, got: {date_str}",
        )


def handle_provider_error(e: ProviderError) -> HTTPException:
    """Convert provider error to HTTP exception."""
    if isinstance(e, ProviderAuthError):
        return HTTPException(
            status_code=401,
            detail={
                "error": "Authentication failed",
                "detail": e.message,
                "source": e.source.value if e.source else None,
            },
        )
    elif isinstance(e, ProviderConfigError):
        return HTTPException(
            status_code=503,
            detail={
                "error": "Provider not configured",
                "detail": e.message,
                "source": e.source.value if e.source else None,
            },
        )
    elif isinstance(e, ProviderAPIError):
        return HTTPException(
            status_code=502,
            detail={
                "error": "External API error",
                "detail": e.message,
                "source": e.source.value if e.source else None,
                "status_code": e.status_code,
            },
        )
    else:
        return HTTPException(
            status_code=500,
            detail={
                "error": "Provider error",
                "detail": e.message,
                "source": e.source.value if e.source else None,
            },
        )


# Endpoints

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Check health status of data intake service and all providers.

    Returns:
        Health status of service and each registered provider
    """
    service = get_data_intake_service()
    source_health = await service.health_check_all()

    return HealthCheckResponse(
        status="healthy" if all(source_health.values()) else "degraded",
        sources={s.value: healthy for s, healthy in source_health.items()},
        timestamp=datetime.utcnow(),
    )


@router.get("/sources", response_model=SourcesListResponse)
async def list_sources():
    """
    List all registered data sources.

    Returns:
        List of available source types
    """
    service = get_data_intake_service()
    sources = service.get_registered_sources()

    return SourcesListResponse(
        sources=[s.value for s in sources],
        count=len(sources),
    )


@router.get("/metrika/visits", response_model=VisitsResponse)
async def get_metrika_visits(
    date_from: str = Query(
        ...,
        description="Start date in YYYY-MM-DD format",
        example="2025-11-01",
    ),
    date_to: str = Query(
        ...,
        description="End date in YYYY-MM-DD format",
        example="2025-11-22",
    ),
    limit: Optional[int] = Query(
        default=None,
        ge=1,
        le=100000,
        description="Maximum number of records to return",
    ),
):
    """
    Fetch visit data from Yandex.Metrika.

    Returns normalized visit events for the specified date range.

    Args:
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        limit: Maximum records (optional, max 100000)

    Returns:
        VisitsResponse with list of normalized VisitEvent objects
    """
    # Parse dates
    start_date = parse_date(date_from, "date_from")
    end_date = parse_date(date_to, "date_to")

    # Validate date range
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="date_from must be before or equal to date_to",
        )

    # Fetch data
    service = get_data_intake_service()

    if not service.is_source_available(SourceType.YANDEX_METRIKA):
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Provider not available",
                "detail": "Yandex.Metrika provider is not configured. "
                         "Set YANDEX_METRIKA_TOKEN and YANDEX_METRIKA_COUNTER_ID environment variables.",
            },
        )

    try:
        visits = await service.fetch_visits_from_source(
            SourceType.YANDEX_METRIKA,
            start_date,
            end_date,
            limit,
        )
    except ProviderError as e:
        logger.error(f"Failed to fetch Metrika visits: {e.message}")
        raise handle_provider_error(e)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return VisitsResponse(
        source=SourceType.YANDEX_METRIKA,
        date_from=date_from,
        date_to=date_to,
        count=len(visits),
        items=visits,
    )


@router.get("/visits", response_model=VisitsResponse)
async def get_all_visits(
    date_from: str = Query(
        ...,
        description="Start date in YYYY-MM-DD format",
        example="2025-11-01",
    ),
    date_to: str = Query(
        ...,
        description="End date in YYYY-MM-DD format",
        example="2025-11-22",
    ),
    source: Optional[str] = Query(
        default=None,
        description="Filter by source type (e.g., YANDEX_METRIKA)",
    ),
    limit: Optional[int] = Query(
        default=None,
        ge=1,
        le=100000,
        description="Maximum number of records per source",
    ),
):
    """
    Fetch visit data from all sources or a specific source.

    Returns normalized visit events aggregated from all registered providers
    or filtered by a specific source.

    Args:
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        source: Optional source filter
        limit: Maximum records per source

    Returns:
        VisitsResponse with aggregated visit events
    """
    # Parse dates
    start_date = parse_date(date_from, "date_from")
    end_date = parse_date(date_to, "date_to")

    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="date_from must be before or equal to date_to",
        )

    service = get_data_intake_service()

    try:
        if source:
            # Validate source type
            try:
                source_type = SourceType(source)
            except ValueError:
                valid_sources = [s.value for s in SourceType]
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid source: {source}. Valid sources: {valid_sources}",
                )

            visits = await service.fetch_visits_from_source(
                source_type,
                start_date,
                end_date,
                limit,
            )
            response_source = source_type
        else:
            visits = await service.fetch_all_visits(
                start_date,
                end_date,
                limit,
            )
            response_source = SourceType.OTHER  # Mixed sources

    except ProviderError as e:
        logger.error(f"Failed to fetch visits: {e.message}")
        raise handle_provider_error(e)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return VisitsResponse(
        source=response_source if source else SourceType.OTHER,
        date_from=date_from,
        date_to=date_to,
        count=len(visits),
        items=visits,
    )


# ============================================================================
# PIPELINE ENDPOINTS (ETL: Raw → Normalized → Features)
# ============================================================================

@router.post("/pipeline/run", response_model=PipelineStatus)
async def run_pipeline(request: PipelineRunRequest):
    """
    Run the full ETL pipeline for a data source.

    Pipeline steps:
    1. Fetch raw data from source API
    2. Save to raw_events (L1)
    3. Normalize to unified format
    4. Save to normalized_events (L2)
    5. Calculate features
    6. Save to feature_store (L3)

    Args:
        request: Pipeline run request with source and date range

    Returns:
        PipelineStatus with execution results
    """
    # Validate source
    try:
        source_type = SourceType(request.source)
    except ValueError:
        valid_sources = [s.value for s in SourceType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source: {request.source}. Valid: {valid_sources}",
        )

    # Parse dates
    start_date = parse_date(request.date_from, "date_from")
    end_date = parse_date(request.date_to, "date_to")

    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="date_from must be before or equal to date_to",
        )

    # Run pipeline
    pipeline = get_pipeline()

    try:
        status = await pipeline.run_full_pipeline(source_type, start_date, end_date)
        return status
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline/retry")
async def retry_pending():
    """
    Process pending raw events that weren't fully processed.

    Useful for retry logic after failures.
    """
    pipeline = get_pipeline()

    try:
        status = await pipeline.process_pending_raw_events()
        return status
    except Exception as e:
        logger.error(f"Retry failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FEATURE STORE ENDPOINTS (L3 - Analytics Agent's Data Source)
# ============================================================================

@router.get("/features", response_model=FeaturesResponse)
async def get_features(
    source: Optional[str] = Query(default=None, description="Filter by source"),
    date_from: Optional[str] = Query(default=None, description="Start date YYYY-MM-DD"),
    date_to: Optional[str] = Query(default=None, description="End date YYYY-MM-DD"),
    min_hot_score: Optional[int] = Query(default=None, ge=0, le=100, description="Minimum hot score"),
    segment_type: Optional[str] = Query(default=None, description="Filter by segment type"),
    limit: int = Query(default=100, ge=1, le=10000, description="Max records to return"),
):
    """
    Get features from Feature Store (L3).

    This is the main endpoint for the Analytics Agent to fetch data.
    The agent should ONLY use Feature Store, not raw or normalized data.

    Args:
        source: Optional filter by source type
        date_from: Optional start date filter
        date_to: Optional end date filter
        min_hot_score: Optional minimum hot_score_base filter
        segment_type: Optional segment filter
        limit: Maximum records to return

    Returns:
        FeaturesResponse with computed features
    """
    storage = get_storage()

    source_type = None
    if source:
        try:
            source_type = SourceType(source)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid source: {source}")

    try:
        features = await storage.get_features(
            source=source_type,
            min_hot_score=min_hot_score,
            segment_type=segment_type,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )

        return FeaturesResponse(
            source=source,
            date_from=date_from,
            date_to=date_to,
            count=len(features),
            items=[f.model_dump() for f in features],
        )
    except StorageError as e:
        logger.error(f"Failed to get features: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features/hot", response_model=HotLeadsResponse)
async def get_hot_leads(
    min_score: int = Query(default=50, ge=0, le=100, description="Minimum hot score"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max records"),
):
    """
    Get hot leads from Feature Store.

    Convenience endpoint for quickly getting high-scoring sessions.

    Note: hot_score_base is the BASE score calculated by data_intake.
    The final hot_score may be adjusted by the Analytics Agent.

    Args:
        min_score: Minimum hot_score_base to include (default: 50)
        limit: Maximum records to return

    Returns:
        HotLeadsResponse with hot leads
    """
    storage = get_storage()

    try:
        features = await storage.get_hot_leads(min_score=min_score, limit=limit)

        return HotLeadsResponse(
            min_score=min_score,
            count=len(features),
            items=[f.model_dump() for f in features],
        )
    except StorageError as e:
        logger.error(f"Failed to get hot leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/normalized")
async def get_normalized_events(
    source: Optional[str] = Query(default=None, description="Filter by source"),
    date_from: Optional[str] = Query(default=None, description="Start date"),
    date_to: Optional[str] = Query(default=None, description="End date"),
    limit: int = Query(default=100, ge=1, le=10000),
):
    """
    Get normalized events from L2 storage.

    Note: Analytics Agent should use /features endpoint instead.
    This endpoint is mainly for debugging and data inspection.
    """
    storage = get_storage()

    source_type = None
    if source:
        try:
            source_type = SourceType(source)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid source: {source}")

    try:
        events = await storage.get_normalized_events(
            source=source_type,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )

        return {
            "source": source,
            "date_from": date_from,
            "date_to": date_to,
            "count": len(events),
            "items": [e.model_dump() for e in events],
        }
    except StorageError as e:
        logger.error(f"Failed to get normalized events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Integration Example
# ============================================================================
#
# To integrate this router with your main FastAPI application:
#
# from fastapi import FastAPI
# from data_intake.routes import router as data_intake_router
#
# app = FastAPI(title="Lead Generation System")
# app.include_router(data_intake_router)
#
# # Or with a prefix:
# app.include_router(data_intake_router, prefix="/api/v1")
#
# This will add the following endpoints:
#
# HEALTH & INFO:
# - GET /data-intake/health
# - GET /data-intake/sources
#
# LEGACY (direct fetch, no storage):
# - GET /data-intake/metrika/visits
# - GET /data-intake/visits
#
# PIPELINE (ETL with 3-layer storage):
# - POST /data-intake/pipeline/run
# - POST /data-intake/pipeline/retry
#
# FEATURE STORE (for Analytics Agent):
# - GET /data-intake/features
# - GET /data-intake/features/hot
# - GET /data-intake/normalized
#
# ============================================================================
