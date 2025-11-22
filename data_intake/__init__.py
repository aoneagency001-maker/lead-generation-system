"""
Data Intake Module

Three-layer data architecture for analytics:
- L1 (Raw): raw_events - data as-is from sources
- L2 (Normalized): normalized_events - unified format
- L3 (Features): feature_store - computed features for analytics

Main principle: This module is a "dumb pipeline" that only collects,
normalizes, and stores data. It does NOT perform deep analysis.
The "Main Analytics Agent" works ONLY with Feature Store (L3).

Quick start:
    # Run pipeline to fetch and process data
    from data_intake.pipeline import get_pipeline

    pipeline = get_pipeline()
    status = await pipeline.run_full_pipeline(
        SourceType.YANDEX_METRIKA,
        date(2025, 11, 1),
        date(2025, 11, 22)
    )

    # Get features for analytics agent
    from data_intake.database.storage import get_storage

    storage = get_storage()
    features = await storage.get_features(min_hot_score=50)

FastAPI integration:
    from data_intake.routes import router as data_intake_router
    app.include_router(data_intake_router)

Endpoints:
    - POST /data-intake/pipeline/run - Run ETL pipeline
    - GET /data-intake/features - Get features (for analytics agent)
    - GET /data-intake/features/hot - Get hot leads
"""

# Models
from data_intake.models import (
    # Enums
    SourceType,
    ProcessingStatus,
    SegmentType,
    DecisionStage,
    TrafficSourceType,
    # L1: Raw
    RawEvent,
    RawEventCreate,
    # L2: Normalized
    NormalizedEvent,
    NormalizedEventCreate,
    # L3: Features
    SessionFeatures,
    SessionFeaturesCreate,
    KeyPagesVisited,
    UserFeatureAggregate,
    # Legacy (backward compatibility)
    BaseEvent,
    VisitEvent,
    PageViewEvent,
    VisitsResponse,
    # Pipeline
    PipelineStatus,
)

# Services
from data_intake.service import (
    DataIntakeService,
    get_data_intake_service,
    reset_data_intake_service,
)

# Pipeline
from data_intake.pipeline import (
    DataIntakePipeline,
    get_pipeline,
    reset_pipeline,
)

# Feature Calculator
from data_intake.feature_calculator import (
    FeatureCalculator,
    get_feature_calculator,
)

# Storage
from data_intake.database.storage import (
    DataIntakeStorage,
    get_storage,
    reset_storage,
    StorageError,
)

__all__ = [
    # Enums
    "SourceType",
    "ProcessingStatus",
    "SegmentType",
    "DecisionStage",
    "TrafficSourceType",
    # L1: Raw Models
    "RawEvent",
    "RawEventCreate",
    # L2: Normalized Models
    "NormalizedEvent",
    "NormalizedEventCreate",
    # L3: Feature Models
    "SessionFeatures",
    "SessionFeaturesCreate",
    "KeyPagesVisited",
    "UserFeatureAggregate",
    # Legacy Models
    "BaseEvent",
    "VisitEvent",
    "PageViewEvent",
    "VisitsResponse",
    # Pipeline
    "PipelineStatus",
    "DataIntakePipeline",
    "get_pipeline",
    "reset_pipeline",
    # Service
    "DataIntakeService",
    "get_data_intake_service",
    "reset_data_intake_service",
    # Feature Calculator
    "FeatureCalculator",
    "get_feature_calculator",
    # Storage
    "DataIntakeStorage",
    "get_storage",
    "reset_storage",
    "StorageError",
]

__version__ = "0.2.0"
