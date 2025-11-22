-- ===================================
-- DATA INTAKE MODULE - DATABASE SCHEMA
-- ===================================
-- Three-layer data architecture:
-- L1: raw_events     - Raw data as-is from sources
-- L2: normalized_events - Unified format
-- L3: feature_store  - Computed features for analytics
--
-- Run via: python scripts/apply_data_intake_schema.py

-- ===================================
-- L1: RAW EVENTS (Сырые данные)
-- ===================================
-- Все данные как есть из источников, без обработки
-- "Любой мусор сохраняется" - это архив всего входящего

CREATE TABLE IF NOT EXISTS raw_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source identification
    source VARCHAR(50) NOT NULL,              -- YANDEX_METRIKA, GOOGLE_ANALYTICS, etc.
    source_event_id VARCHAR(255),             -- Original ID from source
    counter_id VARCHAR(100),                  -- Counter/Property ID

    -- Raw payload
    raw_data JSONB NOT NULL,                  -- Complete raw response from API

    -- Metadata for traceability
    api_endpoint VARCHAR(255),                -- Which API endpoint was called
    api_version VARCHAR(50),                  -- API version used
    request_params JSONB,                     -- Request parameters

    -- Processing status
    processing_status VARCHAR(50) DEFAULT 'pending'
        CHECK (processing_status IN ('pending', 'processed', 'failed', 'skipped')),
    processing_error TEXT,                    -- Error message if failed
    processed_at TIMESTAMP WITH TIME ZONE,

    -- Data range
    date_from DATE,
    date_to DATE,

    -- Pipeline tracking
    pipeline_version VARCHAR(50) DEFAULT '1.0',
    batch_id VARCHAR(100),                    -- For grouping related imports

    -- Timestamps
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for raw_events
CREATE INDEX IF NOT EXISTS idx_raw_events_source ON raw_events(source);
CREATE INDEX IF NOT EXISTS idx_raw_events_status ON raw_events(processing_status);
CREATE INDEX IF NOT EXISTS idx_raw_events_fetched ON raw_events(fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_raw_events_date_range ON raw_events(date_from, date_to);
CREATE INDEX IF NOT EXISTS idx_raw_events_batch ON raw_events(batch_id);

-- ===================================
-- L2: NORMALIZED EVENTS (Нормализованные данные)
-- ===================================
-- Единый формат для всех источников
-- Это "чистые" данные, готовые для feature extraction

CREATE TABLE IF NOT EXISTS normalized_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to raw data (traceability)
    raw_event_id UUID REFERENCES raw_events(id) ON DELETE SET NULL,

    -- Source identification
    source VARCHAR(50) NOT NULL,              -- YANDEX_METRIKA, GOOGLE_ANALYTICS, etc.

    -- Session/User identification
    session_id VARCHAR(255),                  -- Visit/Session ID (may be null)
    user_id VARCHAR(255),                     -- User ID if available
    client_id VARCHAR(255),                   -- Client ID (cookie-based)

    -- Event timing
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    date_only DATE GENERATED ALWAYS AS (occurred_at::date) STORED,

    -- URL data
    url TEXT,
    landing_page TEXT,                        -- First page of session
    exit_page TEXT,                           -- Last page of session

    -- Traffic source
    referrer TEXT,
    utm_source VARCHAR(255),
    utm_medium VARCHAR(255),
    utm_campaign VARCHAR(255),
    utm_term VARCHAR(255),
    utm_content VARCHAR(255),
    traffic_source_type VARCHAR(100),         -- organic, paid, social, direct, referral

    -- Device info
    device_type VARCHAR(50),                  -- desktop, mobile, tablet
    browser VARCHAR(100),
    os VARCHAR(100),
    screen_resolution VARCHAR(50),

    -- Geography
    country VARCHAR(100),
    region VARCHAR(100),
    city VARCHAR(100),

    -- Session metrics (raw, before feature calculation)
    page_views INTEGER,
    raw_visit_duration INTEGER,               -- Duration in seconds (includes AFK!)
    events_count INTEGER,

    -- Behavior flags
    is_new_visitor BOOLEAN,
    is_bounce BOOLEAN,

    -- Search data
    search_phrase TEXT,                       -- If came from search
    internal_search_query TEXT,               -- Site search if any

    -- Goals/Conversions (raw)
    goals_reached JSONB,                      -- List of reached goals

    -- Raw events within session (for detailed analysis)
    raw_hits JSONB,                           -- Array of hits/pageviews with timestamps

    -- Pipeline tracking
    pipeline_version VARCHAR(50) DEFAULT '1.0',
    normalized_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for normalized_events
CREATE INDEX IF NOT EXISTS idx_norm_events_source ON normalized_events(source);
CREATE INDEX IF NOT EXISTS idx_norm_events_session ON normalized_events(session_id);
CREATE INDEX IF NOT EXISTS idx_norm_events_user ON normalized_events(user_id);
CREATE INDEX IF NOT EXISTS idx_norm_events_date ON normalized_events(date_only);
CREATE INDEX IF NOT EXISTS idx_norm_events_occurred ON normalized_events(occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_norm_events_utm_source ON normalized_events(utm_source);
CREATE INDEX IF NOT EXISTS idx_norm_events_traffic_type ON normalized_events(traffic_source_type);
CREATE INDEX IF NOT EXISTS idx_norm_events_device ON normalized_events(device_type);
CREATE INDEX IF NOT EXISTS idx_norm_events_raw ON normalized_events(raw_event_id);

-- GIN index for JSONB columns
CREATE INDEX IF NOT EXISTS idx_norm_events_goals ON normalized_events USING GIN (goals_reached);

-- ===================================
-- L3: FEATURE STORE (Признаки для аналитики)
-- ===================================
-- Вычисленные признаки, готовые для использования агентами
-- "Топливный бак" для аналитического модуля

CREATE TABLE IF NOT EXISTS feature_store (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to normalized event
    normalized_event_id UUID REFERENCES normalized_events(id) ON DELETE CASCADE,

    -- Identification
    source VARCHAR(50) NOT NULL,
    session_id VARCHAR(255),
    user_id VARCHAR(255),
    client_id VARCHAR(255),
    event_date DATE NOT NULL,

    -- ===================================
    -- TIME FEATURES (Временные признаки)
    -- ===================================
    active_time_sec INTEGER,                  -- Реальное активное время (без AFK)
    idle_time_sec INTEGER,                    -- Время бездействия
    time_to_first_action_sec INTEGER,         -- Время до первого клика

    -- ===================================
    -- ENGAGEMENT FEATURES (Вовлеченность)
    -- ===================================
    page_depth INTEGER,                       -- Глубина просмотра (страниц)
    scroll_depth_avg INTEGER,                 -- Средняя глубина прокрутки (0-100)
    clicks_count INTEGER,                     -- Количество кликов

    visit_frequency DECIMAL(5,2),             -- Частота посещений (визиты/неделя)
    days_since_first_visit INTEGER,           -- Дней с первого визита
    days_since_last_visit INTEGER,            -- Дней с последнего визита
    total_visits INTEGER,                     -- Всего визитов

    -- ===================================
    -- INTENT FEATURES (Намерение)
    -- ===================================
    key_pages_visited JSONB,                  -- {"price": true, "guarantee": true, "portfolio": false}
    key_pages_count INTEGER,                  -- Сколько ключевых страниц посетил

    form_interactions INTEGER,                -- Взаимодействия с формами
    cta_clicks INTEGER,                       -- Клики по CTA

    -- ===================================
    -- BOUNCE/RETURN FEATURES
    -- ===================================
    bounce_flag BOOLEAN,                      -- Отказ (да/нет)
    bounce_reason VARCHAR(100),               -- Причина отказа (если определено)
    return_flag BOOLEAN,                      -- Вернувшийся посетитель
    return_interval_days INTEGER,             -- Через сколько дней вернулся

    -- ===================================
    -- SEARCH/PAIN FEATURES
    -- ===================================
    search_pain_points JSONB,                 -- Выделенные "боли" из поисковых запросов
    search_intent_category VARCHAR(100),      -- Категория поискового интента

    -- ===================================
    -- SCORING FEATURES (Базовые скоры)
    -- ===================================
    -- Это БАЗОВЫЕ скоры, НЕ финальный hot_score!
    -- Финальный hot_score считает "Главный Агент Аналитики"

    hot_score_base INTEGER CHECK (hot_score_base BETWEEN 0 AND 100),
    engagement_score INTEGER CHECK (engagement_score BETWEEN 0 AND 100),
    intent_score INTEGER CHECK (intent_score BETWEEN 0 AND 100),

    -- ===================================
    -- SEGMENTATION FEATURES
    -- ===================================
    segment_type VARCHAR(50),                 -- сомневающийся, импульсивный, осторожный, методичный, горячий
    decision_stage VARCHAR(50),               -- awareness, consideration, evaluation, purchase_intent

    -- ===================================
    -- TECHNICAL FEATURES
    -- ===================================
    device_type VARCHAR(50),
    is_mobile BOOLEAN,
    traffic_source_type VARCHAR(100),

    -- ===================================
    -- METADATA
    -- ===================================
    feature_version VARCHAR(50) DEFAULT '1.0', -- Version of feature calculation algorithm
    calculation_notes TEXT,                   -- Notes about calculation (warnings, etc.)

    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for feature_store
CREATE INDEX IF NOT EXISTS idx_features_source ON feature_store(source);
CREATE INDEX IF NOT EXISTS idx_features_session ON feature_store(session_id);
CREATE INDEX IF NOT EXISTS idx_features_user ON feature_store(user_id);
CREATE INDEX IF NOT EXISTS idx_features_date ON feature_store(event_date);
CREATE INDEX IF NOT EXISTS idx_features_hot_score ON feature_store(hot_score_base DESC);
CREATE INDEX IF NOT EXISTS idx_features_segment ON feature_store(segment_type);
CREATE INDEX IF NOT EXISTS idx_features_stage ON feature_store(decision_stage);
CREATE INDEX IF NOT EXISTS idx_features_normalized ON feature_store(normalized_event_id);

-- GIN indexes for JSONB
CREATE INDEX IF NOT EXISTS idx_features_key_pages ON feature_store USING GIN (key_pages_visited);
CREATE INDEX IF NOT EXISTS idx_features_pain_points ON feature_store USING GIN (search_pain_points);

-- ===================================
-- AGGREGATE TABLES (Агрегаты по пользователям)
-- ===================================
-- Агрегированные данные по user_id / client_id

CREATE TABLE IF NOT EXISTS user_feature_aggregates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User identification
    user_id VARCHAR(255),
    client_id VARCHAR(255),

    -- Must have at least one identifier
    CONSTRAINT user_or_client_required CHECK (user_id IS NOT NULL OR client_id IS NOT NULL),

    -- Aggregate metrics
    total_sessions INTEGER DEFAULT 0,
    total_page_views INTEGER DEFAULT 0,
    total_active_time_sec INTEGER DEFAULT 0,

    first_visit_at TIMESTAMP WITH TIME ZONE,
    last_visit_at TIMESTAMP WITH TIME ZONE,

    avg_session_duration_sec DECIMAL(10,2),
    avg_page_depth DECIMAL(5,2),

    -- Behavior patterns
    preferred_device VARCHAR(50),
    preferred_traffic_source VARCHAR(100),

    -- All visited key pages (accumulated)
    all_key_pages_visited JSONB DEFAULT '{}',

    -- Aggregated scores (latest or average)
    current_hot_score INTEGER,
    current_segment_type VARCHAR(50),
    current_decision_stage VARCHAR(50),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for user_feature_aggregates
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_agg_user ON user_feature_aggregates(user_id) WHERE user_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_agg_client ON user_feature_aggregates(client_id) WHERE client_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_user_agg_hot_score ON user_feature_aggregates(current_hot_score DESC);
CREATE INDEX IF NOT EXISTS idx_user_agg_last_visit ON user_feature_aggregates(last_visit_at DESC);

-- ===================================
-- PROCESSING LOG (Лог обработки)
-- ===================================
-- Для отслеживания и дебага ETL pipeline

CREATE TABLE IF NOT EXISTS data_intake_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Operation info
    operation VARCHAR(100) NOT NULL,          -- fetch_raw, normalize, calculate_features
    source VARCHAR(50),

    -- Status
    status VARCHAR(50) NOT NULL CHECK (status IN ('started', 'completed', 'failed', 'partial')),

    -- Metrics
    records_processed INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    duration_ms INTEGER,

    -- Error info
    error_message TEXT,
    error_details JSONB,

    -- Metadata
    batch_id VARCHAR(100),
    pipeline_version VARCHAR(50),

    -- Parameters used
    params JSONB,

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for data_intake_log
CREATE INDEX IF NOT EXISTS idx_intake_log_operation ON data_intake_log(operation);
CREATE INDEX IF NOT EXISTS idx_intake_log_status ON data_intake_log(status);
CREATE INDEX IF NOT EXISTS idx_intake_log_started ON data_intake_log(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_intake_log_batch ON data_intake_log(batch_id);

-- ===================================
-- TRIGGERS
-- ===================================

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP;
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers (if not exist)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_normalized_events_updated_at') THEN
        CREATE TRIGGER update_normalized_events_updated_at
        BEFORE UPDATE ON normalized_events
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_feature_store_updated_at') THEN
        CREATE TRIGGER update_feature_store_updated_at
        BEFORE UPDATE ON feature_store
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_user_aggregates_updated_at') THEN
        CREATE TRIGGER update_user_aggregates_updated_at
        BEFORE UPDATE ON user_feature_aggregates
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- ===================================
-- VIEWS
-- ===================================

-- Hot leads view (for quick access by analytics agent)
CREATE OR REPLACE VIEW hot_leads_features AS
SELECT
    f.id,
    f.session_id,
    f.user_id,
    f.client_id,
    f.event_date,
    f.hot_score_base,
    f.segment_type,
    f.decision_stage,
    f.active_time_sec,
    f.page_depth,
    f.key_pages_visited,
    f.return_flag,
    n.url,
    n.utm_source,
    n.utm_campaign,
    n.device_type
FROM feature_store f
LEFT JOIN normalized_events n ON f.normalized_event_id = n.id
WHERE f.hot_score_base >= 50
ORDER BY f.hot_score_base DESC, f.event_date DESC;

-- Daily intake stats
CREATE OR REPLACE VIEW daily_intake_stats AS
SELECT
    date_trunc('day', fetched_at) as day,
    source,
    COUNT(*) as raw_count,
    SUM(CASE WHEN processing_status = 'processed' THEN 1 ELSE 0 END) as processed_count,
    SUM(CASE WHEN processing_status = 'failed' THEN 1 ELSE 0 END) as failed_count
FROM raw_events
GROUP BY date_trunc('day', fetched_at), source
ORDER BY day DESC;

-- ===================================
-- COMMENTS
-- ===================================
COMMENT ON TABLE raw_events IS 'L1: Raw data layer - all incoming data as-is from sources';
COMMENT ON TABLE normalized_events IS 'L2: Normalized layer - unified event format across all sources';
COMMENT ON TABLE feature_store IS 'L3: Feature layer - computed features for analytics agents';
COMMENT ON TABLE user_feature_aggregates IS 'Aggregated user-level features across sessions';
COMMENT ON TABLE data_intake_log IS 'ETL pipeline processing log for debugging and monitoring';
