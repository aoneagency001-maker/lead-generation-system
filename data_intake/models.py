"""
Data Intake Module - Unified Models

Three-layer data architecture:
- L1 (Raw): RawEvent - data as-is from sources
- L2 (Normalized): NormalizedEvent - unified format
- L3 (Features): SessionFeatures - computed features for analytics

All providers must transform their data through these layers.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================

class SourceType(str, Enum):
    """Supported analytics data sources."""
    YANDEX_METRIKA = "YANDEX_METRIKA"
    GOOGLE_ANALYTICS = "GOOGLE_ANALYTICS"
    YANDEX_MAPS = "YANDEX_MAPS"
    OTHER = "OTHER"


class ProcessingStatus(str, Enum):
    """Processing status for raw events."""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SegmentType(str, Enum):
    """User segment types based on behavior."""
    DOUBTING = "сомневающийся"        # Сомневается, много смотрит, мало кликает
    IMPULSIVE = "импульсивный"        # Быстрые решения, мало страниц
    CAUTIOUS = "осторожный"           # Много читает, проверяет гарантии
    METHODICAL = "методичный"         # Систематично изучает всё
    HOT = "горячий"                   # Явный intent к покупке


class DecisionStage(str, Enum):
    """Customer journey decision stage."""
    AWARENESS = "awareness"           # Узнаёт о проблеме/решении
    CONSIDERATION = "consideration"   # Сравнивает варианты
    EVALUATION = "evaluation"         # Оценивает конкретное предложение
    PURCHASE_INTENT = "purchase_intent"  # Готов к покупке


class TrafficSourceType(str, Enum):
    """Traffic source classification."""
    ORGANIC = "organic"
    PAID = "paid"
    SOCIAL = "social"
    DIRECT = "direct"
    REFERRAL = "referral"
    EMAIL = "email"
    OTHER = "other"


# ============================================================================
# L1: RAW LAYER MODELS
# ============================================================================

class RawEvent(BaseModel):
    """
    L1: Raw event model - data as-is from source API.

    Stores complete raw response without any transformation.
    "Any garbage is saved" - this is the archive of all incoming data.
    """
    id: Optional[str] = Field(default=None, description="Database ID")

    # Source identification
    source: SourceType
    source_event_id: Optional[str] = Field(default=None, description="Original ID from source")
    counter_id: Optional[str] = Field(default=None, description="Counter/Property ID")

    # Raw payload - THE MOST IMPORTANT FIELD
    raw_data: dict[str, Any] = Field(..., description="Complete raw response from API")

    # Metadata for traceability
    api_endpoint: Optional[str] = Field(default=None, description="Which API endpoint was called")
    api_version: Optional[str] = Field(default=None, description="API version used")
    request_params: Optional[dict[str, Any]] = Field(default=None, description="Request parameters")

    # Processing status
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processing_error: Optional[str] = None
    processed_at: Optional[datetime] = None

    # Data range
    date_from: Optional[date] = None
    date_to: Optional[date] = None

    # Pipeline tracking
    pipeline_version: str = "1.0"
    batch_id: Optional[str] = None

    # Timestamps
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: Optional[datetime] = None


class RawEventCreate(BaseModel):
    """Model for creating new raw event."""
    source: SourceType
    source_event_id: Optional[str] = None
    counter_id: Optional[str] = None
    raw_data: dict[str, Any]
    api_endpoint: Optional[str] = None
    api_version: Optional[str] = None
    request_params: Optional[dict[str, Any]] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    batch_id: Optional[str] = None


# ============================================================================
# L2: NORMALIZED LAYER MODELS
# ============================================================================

class NormalizedEvent(BaseModel):
    """
    L2: Normalized event model - unified format across all sources.

    This is the "clean" data layer, ready for feature extraction.
    All sources are transformed to this single schema.
    """
    id: Optional[str] = Field(default=None, description="Database ID")
    raw_event_id: Optional[str] = Field(default=None, description="Link to raw event")

    # Source identification
    source: SourceType

    # Session/User identification
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    client_id: Optional[str] = Field(default=None, description="Cookie-based client ID")

    # Event timing
    occurred_at: datetime

    # URL data
    url: Optional[str] = None
    landing_page: Optional[str] = Field(default=None, description="First page of session")
    exit_page: Optional[str] = Field(default=None, description="Last page of session")

    # Traffic source
    referrer: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    traffic_source_type: Optional[TrafficSourceType] = None

    # Device info
    device_type: Optional[str] = None  # desktop, mobile, tablet
    browser: Optional[str] = None
    os: Optional[str] = None
    screen_resolution: Optional[str] = None

    # Geography
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None

    # Session metrics (raw, before feature calculation)
    page_views: Optional[int] = None
    raw_visit_duration: Optional[int] = Field(
        default=None,
        description="Duration in seconds (includes AFK!)"
    )
    events_count: Optional[int] = None

    # Behavior flags
    is_new_visitor: Optional[bool] = None
    is_bounce: Optional[bool] = None

    # Search data
    search_phrase: Optional[str] = Field(default=None, description="If came from search")
    internal_search_query: Optional[str] = Field(default=None, description="Site search if any")

    # Goals/Conversions (raw)
    goals_reached: Optional[list[str]] = None

    # Raw events within session (for detailed analysis)
    raw_hits: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="Array of hits/pageviews with timestamps"
    )

    # Pipeline tracking
    pipeline_version: str = "1.0"
    normalized_at: datetime = Field(default_factory=datetime.utcnow)


class NormalizedEventCreate(BaseModel):
    """Model for creating normalized event."""
    raw_event_id: Optional[str] = None
    source: SourceType
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    client_id: Optional[str] = None
    occurred_at: datetime
    url: Optional[str] = None
    landing_page: Optional[str] = None
    exit_page: Optional[str] = None
    referrer: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    traffic_source_type: Optional[TrafficSourceType] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    screen_resolution: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    page_views: Optional[int] = None
    raw_visit_duration: Optional[int] = None
    events_count: Optional[int] = None
    is_new_visitor: Optional[bool] = None
    is_bounce: Optional[bool] = None
    search_phrase: Optional[str] = None
    internal_search_query: Optional[str] = None
    goals_reached: Optional[list[str]] = None
    raw_hits: Optional[list[dict[str, Any]]] = None


# ============================================================================
# L3: FEATURE LAYER MODELS
# ============================================================================

class KeyPagesVisited(BaseModel):
    """Key pages visited during session."""
    price: bool = False
    guarantee: bool = False
    portfolio: bool = False
    contacts: bool = False
    about: bool = False
    faq: bool = False
    reviews: bool = False

    model_config = {"extra": "allow"}  # Allow custom pages


class SessionFeatures(BaseModel):
    """
    L3: Session features model - computed features for analytics.

    This is the "fuel tank" for the analytics agent.
    The agent works ONLY with this data, not raw or normalized.

    Note: hot_score_base is a BASE score, NOT the final hot_score!
    The final hot_score is calculated by the "Main Analytics Agent".
    """
    id: Optional[str] = Field(default=None, description="Database ID")
    normalized_event_id: Optional[str] = Field(default=None, description="Link to normalized event")

    # Identification
    source: SourceType
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    client_id: Optional[str] = None
    event_date: date

    # ===================================
    # TIME FEATURES
    # ===================================
    active_time_sec: Optional[int] = Field(
        default=None,
        description="Real active time (without AFK)"
    )
    idle_time_sec: Optional[int] = Field(
        default=None,
        description="Idle/AFK time"
    )
    time_to_first_action_sec: Optional[int] = Field(
        default=None,
        description="Time to first click/action"
    )

    # ===================================
    # ENGAGEMENT FEATURES
    # ===================================
    page_depth: Optional[int] = Field(default=None, description="Pages viewed")
    scroll_depth_avg: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Average scroll depth 0-100%"
    )
    clicks_count: Optional[int] = None

    visit_frequency: Optional[float] = Field(
        default=None,
        description="Visits per week"
    )
    days_since_first_visit: Optional[int] = None
    days_since_last_visit: Optional[int] = None
    total_visits: Optional[int] = None

    # ===================================
    # INTENT FEATURES
    # ===================================
    key_pages_visited: Optional[KeyPagesVisited] = Field(
        default=None,
        description="Which key pages were visited"
    )
    key_pages_count: Optional[int] = Field(
        default=None,
        description="Count of key pages visited"
    )

    form_interactions: Optional[int] = Field(
        default=None,
        description="Form field interactions"
    )
    cta_clicks: Optional[int] = Field(
        default=None,
        description="CTA button clicks"
    )

    # ===================================
    # BOUNCE/RETURN FEATURES
    # ===================================
    bounce_flag: Optional[bool] = None
    bounce_reason: Optional[str] = Field(
        default=None,
        description="Reason for bounce if determined"
    )
    return_flag: Optional[bool] = Field(
        default=None,
        description="Is returning visitor"
    )
    return_interval_days: Optional[int] = Field(
        default=None,
        description="Days since last visit"
    )

    # ===================================
    # SEARCH/PAIN FEATURES
    # ===================================
    search_pain_points: Optional[list[str]] = Field(
        default=None,
        description="Extracted pain points from search queries"
    )
    search_intent_category: Optional[str] = None

    # ===================================
    # SCORING FEATURES (BASE scores only!)
    # ===================================
    hot_score_base: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Base hot score (0-100). Final score calculated by analytics agent!"
    )
    engagement_score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Engagement score (0-100)"
    )
    intent_score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Intent score (0-100)"
    )

    # ===================================
    # SEGMENTATION FEATURES
    # ===================================
    segment_type: Optional[SegmentType] = None
    decision_stage: Optional[DecisionStage] = None

    # ===================================
    # TECHNICAL FEATURES
    # ===================================
    device_type: Optional[str] = None
    is_mobile: Optional[bool] = None
    traffic_source_type: Optional[TrafficSourceType] = None

    # ===================================
    # METADATA
    # ===================================
    feature_version: str = "1.0"
    calculation_notes: Optional[str] = Field(
        default=None,
        description="Notes about calculation (warnings, etc.)"
    )
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


class SessionFeaturesCreate(BaseModel):
    """Model for creating session features."""
    normalized_event_id: Optional[str] = None
    source: SourceType
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    client_id: Optional[str] = None
    event_date: date
    active_time_sec: Optional[int] = None
    idle_time_sec: Optional[int] = None
    page_depth: Optional[int] = None
    key_pages_visited: Optional[dict[str, bool]] = None
    key_pages_count: Optional[int] = None
    bounce_flag: Optional[bool] = None
    return_flag: Optional[bool] = None
    hot_score_base: Optional[int] = None
    engagement_score: Optional[int] = None
    intent_score: Optional[int] = None
    segment_type: Optional[SegmentType] = None
    decision_stage: Optional[DecisionStage] = None
    device_type: Optional[str] = None
    is_mobile: Optional[bool] = None
    traffic_source_type: Optional[TrafficSourceType] = None


# ============================================================================
# USER AGGREGATES
# ============================================================================

class UserFeatureAggregate(BaseModel):
    """Aggregated features across all user sessions."""
    id: Optional[str] = None
    user_id: Optional[str] = None
    client_id: Optional[str] = None

    # Aggregate metrics
    total_sessions: int = 0
    total_page_views: int = 0
    total_active_time_sec: int = 0

    first_visit_at: Optional[datetime] = None
    last_visit_at: Optional[datetime] = None

    avg_session_duration_sec: Optional[float] = None
    avg_page_depth: Optional[float] = None

    # Behavior patterns
    preferred_device: Optional[str] = None
    preferred_traffic_source: Optional[str] = None

    # All visited key pages (accumulated)
    all_key_pages_visited: Optional[dict[str, bool]] = None

    # Current scores
    current_hot_score: Optional[int] = None
    current_segment_type: Optional[SegmentType] = None
    current_decision_stage: Optional[DecisionStage] = None


# ============================================================================
# LEGACY MODELS (for backward compatibility with existing code)
# ============================================================================

class BaseEvent(BaseModel):
    """
    Base event model - LEGACY, use NormalizedEvent instead.
    Kept for backward compatibility.
    """
    event_id: Optional[str] = None
    source: SourceType
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    occurred_at: datetime
    url: Optional[str] = None
    referrer: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    user_agent: Optional[str] = None
    ip: Optional[str] = None


class VisitEvent(BaseEvent):
    """
    Visit event model - LEGACY, use NormalizedEvent instead.
    Kept for backward compatibility with existing routes.
    """
    visit_number: Optional[int] = None
    page_views: Optional[int] = None
    active_time_sec: Optional[int] = None
    is_new_visitor: Optional[bool] = None
    bounce: Optional[bool] = None
    # Extended fields for GA4 compatibility
    country: Optional[str] = None
    city: Optional[str] = None
    device_type: Optional[str] = None
    bounce_rate: Optional[float] = None


class PageViewEvent(BaseEvent):
    """Page view event - LEGACY."""
    page_title: Optional[str] = None
    time_on_page_sec: Optional[int] = None


# ============================================================================
# API RESPONSE MODELS
# ============================================================================

class VisitsResponse(BaseModel):
    """Response model for visits endpoint."""
    source: SourceType
    date_from: str
    date_to: str
    count: int
    items: list[VisitEvent]


class PipelineStatus(BaseModel):
    """Pipeline execution status."""
    batch_id: str
    status: str
    raw_count: int = 0
    normalized_count: int = 0
    features_count: int = 0
    errors: list[str] = Field(default_factory=list)
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
