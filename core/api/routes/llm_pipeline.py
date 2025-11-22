"""
LLM Pipeline API Routes

Endpoints for 3-layer LLM processing:
- L2: Normalization (GPT-4)
- L3: Feature Engineering (Claude)
- L4: Analysis & Insights (Perplexity/Claude)
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import logging

from core.database.supabase_client import get_supabase_client

router = APIRouter(prefix="/llm", tags=["LLM Pipeline"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class NormalizationRequest(BaseModel):
    """Request for L2 normalization."""
    raw_event_ids: Optional[List[str]] = Field(None, description="Specific event IDs to process")
    date_from: Optional[date] = Field(None, description="Start date for batch processing")
    date_to: Optional[date] = Field(None, description="End date for batch processing")
    batch_size: int = Field(50, ge=1, le=100, description="Batch size for LLM calls")
    source: Optional[str] = Field(None, description="Filter by source: google_analytics, yandex_metrika")


class FeatureRequest(BaseModel):
    """Request for L3 feature engineering."""
    normalized_event_ids: Optional[List[str]] = Field(None, description="Specific normalized events")
    date_from: Optional[date] = Field(None, description="Start date")
    date_to: Optional[date] = Field(None, description="End date")
    batch_size: int = Field(30, ge=1, le=50, description="Batch size for LLM calls")


class InsightRequest(BaseModel):
    """Request for L4 insights generation."""
    date_from: date = Field(..., description="Analysis start date")
    date_to: date = Field(..., description="Analysis end date")
    insight_type: str = Field("daily", description="daily, weekly, monthly, custom")


class PipelineRequest(BaseModel):
    """Request for full pipeline run."""
    date_from: date = Field(..., description="Start date")
    date_to: date = Field(..., description="End date")
    source: Optional[str] = Field(None, description="Filter by source")
    run_l4: bool = Field(True, description="Generate L4 insights")
    async_mode: bool = Field(False, description="Run in background")


class ProcessingResponse(BaseModel):
    """Response for processing requests."""
    status: str
    task_id: Optional[str] = None
    layer: Optional[str] = None
    records_processed: int = 0
    tokens_used: Dict[str, int] = {}
    processing_time_sec: Optional[float] = None
    message: Optional[str] = None


class InsightResponse(BaseModel):
    """Response for insight generation."""
    status: str
    insight_id: Optional[str] = None
    executive_summary: Optional[str] = None
    key_findings_count: int = 0
    model_used: Optional[str] = None
    generated_at: Optional[str] = None


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@router.get("/status")
async def get_llm_status():
    """
    Check LLM services status and API key availability.

    Returns simplified format + detailed breakdown.
    """
    import os

    openai_key = bool(os.getenv("OPENAI_API_KEY"))
    anthropic_key = bool(os.getenv("ANTHROPIC_API_KEY"))
    perplexity_key = bool(os.getenv("PERPLEXITY_API_KEY"))

    # Simplified status (as requested)
    simple_status = {
        "openai": openai_key,
        "anthropic": anthropic_key,
        "perplexity": perplexity_key,
    }

    # Detailed status by layer
    layers = {
        "l2_normalization": {
            "model": os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
            "provider": "openai",
            "api_key_configured": openai_key,
            "status": "ready" if openai_key else "not_configured"
        },
        "l3_features": {
            "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            "provider": "anthropic",
            "api_key_configured": anthropic_key,
            "status": "ready" if anthropic_key else "not_configured"
        },
        "l4_analysis": {
            "model": os.getenv("PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online"),
            "provider": "perplexity",
            "api_key_configured": perplexity_key,
            "fallback": "claude-3-5-sonnet" if anthropic_key else None,
            "status": "ready" if (perplexity_key or anthropic_key) else "not_configured"
        }
    }

    all_ready = all(
        s["status"] == "ready"
        for s in layers.values()
    )

    return {
        **simple_status,  # openai, anthropic, perplexity as top-level
        "overall_status": "ready" if all_ready else "partial",
        "layers": layers
    }


@router.get("/queue")
async def get_processing_queue():
    """
    Get current LLM processing queue status.
    """
    try:
        supabase = get_supabase_client()

        # Get queue stats
        pending = supabase.table("llm_processing_queue")\
            .select("id", count="exact")\
            .eq("status", "pending")\
            .execute()

        processing = supabase.table("llm_processing_queue")\
            .select("id", count="exact")\
            .eq("status", "processing")\
            .execute()

        completed_today = supabase.table("llm_processing_queue")\
            .select("id", count="exact")\
            .eq("status", "completed")\
            .gte("completed_at", date.today().isoformat())\
            .execute()

        return {
            "queue_status": {
                "pending": pending.count or 0,
                "processing": processing.count or 0,
                "completed_today": completed_today.count or 0
            }
        }
    except Exception as e:
        logger.error(f"Failed to get queue status: {e}")
        return {"error": str(e), "queue_status": None}


# ============================================================================
# L2: Normalization Endpoints
# ============================================================================

@router.post("/normalize", response_model=ProcessingResponse)
async def normalize_events(request: NormalizationRequest):
    """
    L2: Normalize raw events using GPT-4.

    Transforms raw GA4/Metrika events into unified format.
    """
    try:
        from data_intake.llm import NormalizationService

        supabase = get_supabase_client()

        # Fetch raw events
        query = supabase.table("raw_events").select("*")

        if request.raw_event_ids:
            query = query.in_("id", request.raw_event_ids)
        elif request.date_from and request.date_to:
            query = query.gte("occurred_at", request.date_from.isoformat())\
                        .lte("occurred_at", request.date_to.isoformat())
        else:
            # Default: last 24 hours
            query = query.gte("occurred_at", (datetime.now().date()).isoformat())

        if request.source:
            query = query.eq("source", request.source)

        query = query.eq("is_normalized", False).limit(500)
        result = query.execute()

        if not result.data:
            return ProcessingResponse(
                status="no_data",
                layer="L2",
                message="No raw events to normalize"
            )

        # Process with LLM
        normalizer = NormalizationService()
        processed = await normalizer.normalize_batch(
            raw_events=result.data,
            batch_size=request.batch_size
        )

        # Store normalized events
        normalized_events = processed.get("normalized_events", [])
        if normalized_events:
            # Insert into normalized_events table
            supabase.table("normalized_events").insert(normalized_events).execute()

            # Mark raw events as normalized
            raw_ids = [e.get("raw_event_id") for e in normalized_events if e.get("raw_event_id")]
            if raw_ids:
                supabase.table("raw_events")\
                    .update({"is_normalized": True})\
                    .in_("id", raw_ids)\
                    .execute()

        return ProcessingResponse(
            status="completed",
            layer="L2",
            records_processed=len(normalized_events),
            tokens_used=processed.get("tokens", {}),
            message=f"Normalized {len(normalized_events)} events"
        )

    except Exception as e:
        logger.error(f"Normalization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# L3: Feature Engineering Endpoints
# ============================================================================

@router.post("/features", response_model=ProcessingResponse)
async def calculate_features(request: FeatureRequest):
    """
    L3: Calculate session features using Claude.

    Computes hot_score, intent_score, segment classification.
    """
    try:
        from data_intake.llm import FeatureService
        from data_intake.models import NormalizedEvent

        supabase = get_supabase_client()

        # Fetch normalized events
        query = supabase.table("normalized_events").select("*")

        if request.normalized_event_ids:
            query = query.in_("id", request.normalized_event_ids)
        elif request.date_from and request.date_to:
            query = query.gte("occurred_at", request.date_from.isoformat())\
                        .lte("occurred_at", request.date_to.isoformat())

        query = query.eq("has_features", False).limit(300)
        result = query.execute()

        if not result.data:
            return ProcessingResponse(
                status="no_data",
                layer="L3",
                message="No normalized events to process"
            )

        # Convert to NormalizedEvent models
        events = []
        for row in result.data:
            try:
                event = NormalizedEvent(**row)
                events.append(event)
            except Exception as e:
                logger.warning(f"Failed to parse event: {e}")

        # Process with LLM
        feature_service = FeatureService()
        processed = await feature_service.calculate_features_batch(
            normalized_events=events,
            batch_size=request.batch_size
        )

        # Store features
        features = processed.get("features", [])
        if features:
            # Insert into feature_store table
            supabase.table("feature_store").insert(features).execute()

            # Mark normalized events as processed
            event_ids = [f.get("normalized_event_id") for f in features if f.get("normalized_event_id")]
            if event_ids:
                supabase.table("normalized_events")\
                    .update({"has_features": True})\
                    .in_("id", event_ids)\
                    .execute()

        return ProcessingResponse(
            status="completed",
            layer="L3",
            records_processed=len(features),
            tokens_used=processed.get("tokens", {}),
            message=f"Calculated features for {len(features)} sessions"
        )

    except Exception as e:
        logger.error(f"Feature calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# L4: Analysis Endpoints
# ============================================================================

@router.post("/insights", response_model=InsightResponse)
async def generate_insights(request: InsightRequest):
    """
    L4: Generate business insights using Perplexity/Claude.

    Creates executive summary, recommendations, segment analysis.
    """
    try:
        from data_intake.llm import AnalysisService

        supabase = get_supabase_client()

        # Fetch unified metrics
        unified = supabase.table("unified_metrics")\
            .select("*")\
            .gte("date", request.date_from.isoformat())\
            .lte("date", request.date_to.isoformat())\
            .execute()

        # Fetch feature store
        features = supabase.table("feature_store")\
            .select("*")\
            .gte("event_date", request.date_from.isoformat())\
            .lte("event_date", request.date_to.isoformat())\
            .limit(1000)\
            .execute()

        if not unified.data and not features.data:
            return InsightResponse(
                status="no_data",
                message="No data available for analysis"
            )

        # Generate insights
        analyzer = AnalysisService()
        result = await analyzer.generate_insights(
            unified_metrics=unified.data or [],
            feature_store=features.data or [],
            date_from=request.date_from,
            date_to=request.date_to,
            insight_type=request.insight_type,
        )

        # Store insight
        if result.get("insights"):
            record = analyzer.to_analytics_insight_record(result)
            insert_result = supabase.table("analytics_insights").insert(record).execute()
            insight_id = insert_result.data[0]["id"] if insert_result.data else None
        else:
            insight_id = None

        insights = result.get("insights", {})

        return InsightResponse(
            status="completed" if insights else "failed",
            insight_id=insight_id,
            executive_summary=insights.get("executive_summary"),
            key_findings_count=len(insights.get("key_findings", [])),
            model_used=result.get("model_used"),
            generated_at=result.get("generated_at")
        )

    except Exception as e:
        logger.error(f"Insight generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/latest")
async def get_latest_insights(limit: int = 5):
    """
    Get latest generated insights.
    """
    try:
        supabase = get_supabase_client()

        result = supabase.table("analytics_insights")\
            .select("id, date_from, date_to, insight_type, executive_summary, model_used, generated_at")\
            .eq("status", "completed")\
            .order("generated_at", desc=True)\
            .limit(limit)\
            .execute()

        return {"insights": result.data or []}

    except Exception as e:
        logger.error(f"Failed to fetch insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/{insight_id}")
async def get_insight_detail(insight_id: str):
    """
    Get full insight by ID.
    """
    try:
        supabase = get_supabase_client()

        result = supabase.table("analytics_insights")\
            .select("*")\
            .eq("id", insight_id)\
            .single()\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Insight not found")

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch insight: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Full Pipeline Endpoints
# ============================================================================

@router.post("/pipeline/run")
async def run_full_pipeline(
    request: PipelineRequest,
    background_tasks: BackgroundTasks
):
    """
    Run full LLM pipeline: L2 → L3 → L4.

    Can run synchronously or in background.
    """
    from uuid import uuid4

    task_id = str(uuid4())[:8]

    if request.async_mode:
        # Queue for background processing
        try:
            supabase = get_supabase_client()

            queue_record = {
                "task_type": "full_pipeline",
                "layer": "L2",
                "input_type": "raw_events",
                "input_ids": [],
                "model_preference": None,
                "priority": 5,
                "status": "pending"
            }

            supabase.table("llm_processing_queue").insert(queue_record).execute()

            return {
                "status": "queued",
                "task_id": task_id,
                "message": "Pipeline queued for background processing"
            }
        except Exception as e:
            logger.error(f"Failed to queue pipeline: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Synchronous execution
    try:
        from data_intake.llm import LLMPipeline
        from data_intake.models import VisitEvent

        supabase = get_supabase_client()

        # Fetch normalized events (they have occurred_at and all needed fields)
        # Note: raw_events doesn't have occurred_at, url, utm_source - these are in normalized_events
        query = supabase.table("normalized_events")\
            .select("*")\
            .gte("occurred_at", request.date_from.isoformat())\
            .lte("occurred_at", request.date_to.isoformat())

        if request.source:
            query = query.eq("source", request.source)

        query = query.limit(500).order("occurred_at", desc=False)
        result = query.execute()

        if not result.data:
            # Check if there are any raw_events that could be normalized first
            raw_check = supabase.table("raw_events")\
                .select("id", count="exact")\
                .gte("date_from", request.date_from.isoformat())\
                .lte("date_to", request.date_to.isoformat())\
                .limit(1)\
                .execute()
            
            if raw_check.count and raw_check.count > 0:
                return {
                    "status": "needs_normalization",
                    "task_id": task_id,
                    "message": f"Found {raw_check.count} raw events but no normalized events. Please run data intake pipeline first to normalize raw events.",
                    "raw_events_count": raw_check.count,
                    "suggestion": "Run /api/data-intake/pipeline/run to normalize raw events first"
                }
            
            return {
                "status": "no_data",
                "task_id": task_id,
                "message": f"No events found for period {request.date_from} to {request.date_to}. Please ensure data is imported first.",
                "date_from": request.date_from.isoformat(),
                "date_to": request.date_to.isoformat(),
                "suggestion": "Import data from GA4 or Yandex Metrika first, then normalize it"
            }

        # Convert to VisitEvent
        raw_events = []
        for row in result.data:
            try:
                # Parse occurred_at (required field)
                occurred_at = None
                if row.get("occurred_at"):
                    if isinstance(row["occurred_at"], str):
                        # Handle ISO format strings
                        occurred_at_str = row["occurred_at"].replace("Z", "+00:00")
                        occurred_at = datetime.fromisoformat(occurred_at_str)
                    else:
                        occurred_at = row["occurred_at"]
                else:
                    # Fallback to created_at if occurred_at is missing
                    if row.get("created_at"):
                        if isinstance(row["created_at"], str):
                            occurred_at = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
                        else:
                            occurred_at = row["created_at"]
                    else:
                        occurred_at = datetime.utcnow()
                
                # Parse source (required field)
                source_value = row.get("source")
                if not source_value:
                    logger.warning(f"Skipping event {row.get('id')}: missing source")
                    continue
                
                event = VisitEvent(
                    event_id=row.get("id"),
                    source=source_value,
                    user_id=row.get("user_id"),
                    session_id=row.get("session_id"),
                    occurred_at=occurred_at,
                    url=row.get("url"),
                    referrer=row.get("referrer"),
                    utm_source=row.get("utm_source"),
                    utm_medium=row.get("utm_medium"),
                    utm_campaign=row.get("utm_campaign"),
                    is_new_visitor=row.get("is_new_visitor"),
                    page_views=row.get("page_views"),
                    active_time_sec=row.get("raw_visit_duration"),  # Use raw_visit_duration as active_time_sec
                    country=row.get("country"),
                    city=row.get("city"),
                    device_type=row.get("device_type"),
                )
                raw_events.append(event)
            except Exception as e:
                logger.warning(f"Failed to parse normalized event {row.get('id')}: {e}")

        # Run pipeline
        pipeline = LLMPipeline(db_client=supabase)
        pipeline_result = await pipeline.run_full_pipeline(
            raw_events=raw_events,
            date_from=request.date_from,
            date_to=request.date_to,
            generate_insights=request.run_l4,
        )

        return {
            "status": pipeline_result.get("status", "completed"),
            "task_id": task_id,
            "pipeline_id": pipeline_result.get("pipeline_id"),
            "layers": pipeline_result.get("layers", {}),
            "total_tokens": pipeline_result.get("total_tokens", {}),
            "processing_time_sec": pipeline_result.get("total_processing_time_sec")
        }

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
