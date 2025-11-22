-- ============================================================================
-- ОБЪЕДИНЁННЫЕ СХЕМЫ ДЛЯ ПРИМЕНЕНИЯ В SUPABASE
-- ============================================================================
-- Скопируйте этот файл и выполните в Supabase Dashboard → SQL Editor
-- URL: https://app.supabase.com/project/YOUR_PROJECT/sql/new
-- ============================================================================

-- ============================================================================
-- ЧАСТЬ 1: VISITOR TRACKING
-- ============================================================================

-- Посетители сайта
CREATE TABLE IF NOT EXISTS visitors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255),
    page TEXT,
    landing_page TEXT,
    referrer TEXT,
    screen_resolution VARCHAR(50),
    ip_address VARCHAR(45),
    user_agent TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    device_type VARCHAR(20) CHECK (device_type IN ('mobile', 'tablet', 'desktop')),

    -- UTM метки
    utm_source VARCHAR(255),
    utm_medium VARCHAR(255),
    utm_campaign VARCHAR(255),
    utm_term VARCHAR(255),
    utm_content VARCHAR(255),

    -- Флаги
    is_first_visit BOOLEAN DEFAULT false,
    is_bot BOOLEAN DEFAULT false,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_visitors_session_id ON visitors(session_id);
CREATE INDEX IF NOT EXISTS idx_visitors_created_at ON visitors(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_visitors_ip_address ON visitors(ip_address);
CREATE INDEX IF NOT EXISTS idx_visitors_is_bot ON visitors(is_bot);
CREATE INDEX IF NOT EXISTS idx_visitors_device_type ON visitors(device_type);

-- Tilda webhooks (если нужна leads таблица - она должна уже существовать)
CREATE TABLE IF NOT EXISTS tilda_webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID,
    form_name VARCHAR(255),
    page_url TEXT,
    ip_address VARCHAR(45),
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tilda_webhooks_lead_id ON tilda_webhooks(lead_id);
CREATE INDEX IF NOT EXISTS idx_tilda_webhooks_created_at ON tilda_webhooks(created_at DESC);

COMMENT ON TABLE visitors IS 'Посетители сайта - данные для аналитики';
COMMENT ON TABLE tilda_webhooks IS 'Webhook запросы от Tilda';

-- ============================================================================
-- ЧАСТЬ 2: DATA INTAKE (3-LAYER ANALYTICS)
-- ============================================================================

-- L1: RAW EVENTS (Сырые данные)
CREATE TABLE IF NOT EXISTS raw_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) NOT NULL,
    source_event_id VARCHAR(255),
    counter_id VARCHAR(100),
    raw_data JSONB NOT NULL,
    api_endpoint VARCHAR(255),
    api_version VARCHAR(50),
    request_params JSONB,
    processing_status VARCHAR(50) DEFAULT 'pending'
        CHECK (processing_status IN ('pending', 'processed', 'failed', 'skipped')),
    processing_error TEXT,
    processed_at TIMESTAMP WITH TIME ZONE,
    date_from DATE,
    date_to DATE,
    pipeline_version VARCHAR(50) DEFAULT '1.0',
    batch_id VARCHAR(100),
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_raw_events_source ON raw_events(source);
CREATE INDEX IF NOT EXISTS idx_raw_events_status ON raw_events(processing_status);
CREATE INDEX IF NOT EXISTS idx_raw_events_fetched ON raw_events(fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_raw_events_date_range ON raw_events(date_from, date_to);
CREATE INDEX IF NOT EXISTS idx_raw_events_batch ON raw_events(batch_id);

-- L2: NORMALIZED EVENTS
CREATE TABLE IF NOT EXISTS normalized_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_event_id UUID REFERENCES raw_events(id) ON DELETE SET NULL,
    source VARCHAR(50) NOT NULL,
    session_id VARCHAR(255),
    user_id VARCHAR(255),
    client_id VARCHAR(255),
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    url TEXT,
    landing_page TEXT,
    exit_page TEXT,
    referrer TEXT,
    utm_source VARCHAR(255),
    utm_medium VARCHAR(255),
    utm_campaign VARCHAR(255),
    utm_term VARCHAR(255),
    utm_content VARCHAR(255),
    traffic_source_type VARCHAR(100),
    device_type VARCHAR(50),
    browser VARCHAR(100),
    os VARCHAR(100),
    screen_resolution VARCHAR(50),
    country VARCHAR(100),
    region VARCHAR(100),
    city VARCHAR(100),
    page_views INTEGER,
    raw_visit_duration INTEGER,
    events_count INTEGER,
    is_new_visitor BOOLEAN,
    is_bounce BOOLEAN,
    search_phrase TEXT,
    internal_search_query TEXT,
    goals_reached JSONB,
    raw_hits JSONB,
    pipeline_version VARCHAR(50) DEFAULT '1.0',
    normalized_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_norm_events_source ON normalized_events(source);
CREATE INDEX IF NOT EXISTS idx_norm_events_session ON normalized_events(session_id);
CREATE INDEX IF NOT EXISTS idx_norm_events_user ON normalized_events(user_id);
CREATE INDEX IF NOT EXISTS idx_norm_events_occurred ON normalized_events(occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_norm_events_utm_source ON normalized_events(utm_source);
CREATE INDEX IF NOT EXISTS idx_norm_events_traffic_type ON normalized_events(traffic_source_type);
CREATE INDEX IF NOT EXISTS idx_norm_events_device ON normalized_events(device_type);
CREATE INDEX IF NOT EXISTS idx_norm_events_raw ON normalized_events(raw_event_id);
CREATE INDEX IF NOT EXISTS idx_norm_events_goals ON normalized_events USING GIN (goals_reached);

-- L3: FEATURE STORE
CREATE TABLE IF NOT EXISTS feature_store (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    normalized_event_id UUID REFERENCES normalized_events(id) ON DELETE CASCADE,
    source VARCHAR(50) NOT NULL,
    session_id VARCHAR(255),
    user_id VARCHAR(255),
    client_id VARCHAR(255),
    event_date DATE NOT NULL,

    -- Time features
    active_time_sec INTEGER,
    idle_time_sec INTEGER,
    time_to_first_action_sec INTEGER,

    -- Engagement features
    page_depth INTEGER,
    scroll_depth_avg INTEGER,
    clicks_count INTEGER,
    visit_frequency DECIMAL(5,2),
    days_since_first_visit INTEGER,
    days_since_last_visit INTEGER,
    total_visits INTEGER,

    -- Intent features
    key_pages_visited JSONB,
    key_pages_count INTEGER,
    form_interactions INTEGER,
    cta_clicks INTEGER,

    -- Bounce/return features
    bounce_flag BOOLEAN,
    bounce_reason VARCHAR(100),
    return_flag BOOLEAN,
    return_interval_days INTEGER,

    -- Search features
    search_pain_points JSONB,
    search_intent_category VARCHAR(100),

    -- Scoring features (BASE only!)
    hot_score_base INTEGER CHECK (hot_score_base BETWEEN 0 AND 100),
    engagement_score INTEGER CHECK (engagement_score BETWEEN 0 AND 100),
    intent_score INTEGER CHECK (intent_score BETWEEN 0 AND 100),

    -- Segmentation features
    segment_type VARCHAR(50),
    decision_stage VARCHAR(50),

    -- Technical features
    device_type VARCHAR(50),
    is_mobile BOOLEAN,
    traffic_source_type VARCHAR(100),

    -- Metadata
    feature_version VARCHAR(50) DEFAULT '1.0',
    calculation_notes TEXT,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_features_source ON feature_store(source);
CREATE INDEX IF NOT EXISTS idx_features_session ON feature_store(session_id);
CREATE INDEX IF NOT EXISTS idx_features_user ON feature_store(user_id);
CREATE INDEX IF NOT EXISTS idx_features_date ON feature_store(event_date);
CREATE INDEX IF NOT EXISTS idx_features_hot_score ON feature_store(hot_score_base DESC);
CREATE INDEX IF NOT EXISTS idx_features_segment ON feature_store(segment_type);
CREATE INDEX IF NOT EXISTS idx_features_stage ON feature_store(decision_stage);
CREATE INDEX IF NOT EXISTS idx_features_normalized ON feature_store(normalized_event_id);
CREATE INDEX IF NOT EXISTS idx_features_key_pages ON feature_store USING GIN (key_pages_visited);
CREATE INDEX IF NOT EXISTS idx_features_pain_points ON feature_store USING GIN (search_pain_points);

-- User aggregates
CREATE TABLE IF NOT EXISTS user_feature_aggregates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),
    client_id VARCHAR(255),
    CONSTRAINT user_or_client_required CHECK (user_id IS NOT NULL OR client_id IS NOT NULL),
    total_sessions INTEGER DEFAULT 0,
    total_page_views INTEGER DEFAULT 0,
    total_active_time_sec INTEGER DEFAULT 0,
    first_visit_at TIMESTAMP WITH TIME ZONE,
    last_visit_at TIMESTAMP WITH TIME ZONE,
    avg_session_duration_sec DECIMAL(10,2),
    avg_page_depth DECIMAL(5,2),
    preferred_device VARCHAR(50),
    preferred_traffic_source VARCHAR(100),
    all_key_pages_visited JSONB DEFAULT '{}',
    current_hot_score INTEGER,
    current_segment_type VARCHAR(50),
    current_decision_stage VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_agg_user ON user_feature_aggregates(user_id) WHERE user_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_agg_client ON user_feature_aggregates(client_id) WHERE client_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_user_agg_hot_score ON user_feature_aggregates(current_hot_score DESC);
CREATE INDEX IF NOT EXISTS idx_user_agg_last_visit ON user_feature_aggregates(last_visit_at DESC);

-- Processing log
CREATE TABLE IF NOT EXISTS data_intake_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation VARCHAR(100) NOT NULL,
    source VARCHAR(50),
    status VARCHAR(50) NOT NULL CHECK (status IN ('started', 'completed', 'failed', 'partial')),
    records_processed INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    duration_ms INTEGER,
    error_message TEXT,
    error_details JSONB,
    batch_id VARCHAR(100),
    pipeline_version VARCHAR(50),
    params JSONB,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_intake_log_operation ON data_intake_log(operation);
CREATE INDEX IF NOT EXISTS idx_intake_log_status ON data_intake_log(status);
CREATE INDEX IF NOT EXISTS idx_intake_log_started ON data_intake_log(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_intake_log_batch ON data_intake_log(batch_id);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP;
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers (safe - checks if exists)
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

-- Views
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

-- Comments
COMMENT ON TABLE raw_events IS 'L1: Raw data layer - all incoming data as-is from sources';
COMMENT ON TABLE normalized_events IS 'L2: Normalized layer - unified event format across all sources';
COMMENT ON TABLE feature_store IS 'L3: Feature layer - computed features for analytics agents';
COMMENT ON TABLE user_feature_aggregates IS 'Aggregated user-level features across sessions';
COMMENT ON TABLE data_intake_log IS 'ETL pipeline processing log for debugging and monitoring';

-- ============================================================================
-- ГОТОВО! Все таблицы созданы.
-- ============================================================================
