-- ============================================================================
-- UNIFIED ANALYTICS SCHEMA
-- ============================================================================
-- Tables for unified GA4 + Yandex Metrika data and AI-generated insights
-- Run this in Supabase Dashboard -> SQL Editor
-- ============================================================================

-- ============================================================================
-- PART 1: UNIFIED METRICS (Merged GA4 + Metrika data)
-- ============================================================================

CREATE TABLE IF NOT EXISTS unified_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,

    -- Source data (raw from each source)
    ga4_sessions INTEGER,
    ga4_users INTEGER,
    ga4_pageviews INTEGER,
    metrika_visits INTEGER,
    metrika_visitors INTEGER,
    metrika_pageviews INTEGER,

    -- Unified metrics (reconciled/merged)
    unified_sessions INTEGER NOT NULL,
    unified_users INTEGER NOT NULL,
    unified_pageviews INTEGER NOT NULL,

    -- Traffic breakdown by type (JSONB for flexibility)
    -- Structure: {"organic": {"ga4": 50, "metrika": 48, "unified": 49}, ...}
    traffic_breakdown JSONB DEFAULT '{}',

    -- Engagement metrics
    engagement_rate DECIMAL(5,4),       -- 0.0000 to 1.0000
    bounce_rate DECIMAL(5,4),           -- 0.0000 to 1.0000
    avg_session_duration INTEGER,       -- seconds

    -- Conversion data
    conversions INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5,4),       -- 0.0000 to 1.0000
    revenue DECIMAL(12,2),

    -- Scoring (from L3 feature_store aggregation)
    avg_hot_score DECIMAL(4,2),         -- 0.00 to 10.00
    avg_intent_score DECIMAL(4,2),      -- 0.00 to 10.00
    avg_quality_index DECIMAL(5,4),     -- 0.0000 to 1.0000

    -- Dominant segment for the day
    dominant_segment VARCHAR(50),       -- URGENCY, DECISION, PROBLEM, INFO, BRAND

    -- Data quality indicators
    ga4_data_available BOOLEAN DEFAULT false,
    metrika_data_available BOOLEAN DEFAULT false,
    data_quality_score DECIMAL(3,2),    -- 0.00 to 1.00

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Ensure one record per date
    CONSTRAINT unified_metrics_date_unique UNIQUE(date)
);

-- Indexes for unified_metrics
CREATE INDEX IF NOT EXISTS idx_unified_metrics_date ON unified_metrics(date DESC);
CREATE INDEX IF NOT EXISTS idx_unified_metrics_segment ON unified_metrics(dominant_segment);
CREATE INDEX IF NOT EXISTS idx_unified_metrics_hot_score ON unified_metrics(avg_hot_score DESC);

-- ============================================================================
-- PART 2: ANALYTICS INSIGHTS (AI-generated analysis - L4)
-- ============================================================================

CREATE TABLE IF NOT EXISTS analytics_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Analysis period
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,

    -- Analysis type
    insight_type VARCHAR(50) NOT NULL DEFAULT 'daily'
        CHECK (insight_type IN ('daily', 'weekly', 'monthly', 'custom', 'realtime')),

    -- Executive summary (human-readable)
    executive_summary TEXT,

    -- Structured findings (JSONB)
    -- Structure: [{"title": "...", "insight": "...", "impact": "HIGH", "data_points": {...}}]
    key_findings JSONB DEFAULT '[]',

    -- Comparative analysis (GA4 vs Metrika)
    -- Structure: {"ga4_advantages": [...], "metrika_advantages": [...], "discrepancies": [...]}
    comparative_analysis JSONB DEFAULT '{}',

    -- Segment performance breakdown
    -- Structure: {"URGENCY": {"volume": 100, "conversion_rate": 0.05, ...}, ...}
    segment_performance JSONB DEFAULT '{}',

    -- Recommendations
    -- Structure: {"immediate_actions": [...], "opportunities": [...], "risks": [...]}
    recommendations JSONB DEFAULT '{}',

    -- Source citations (for Perplexity Sonar)
    -- Structure: [{"claim": "...", "sources": ["...", "..."]}]
    citations JSONB DEFAULT '[]',

    -- LLM metadata
    model_used VARCHAR(100),            -- "claude-3.5-sonnet", "gpt-4-strict", "perplexity-sonar"
    prompt_version VARCHAR(50),         -- "v1.0", "v1.1"
    tokens_input INTEGER,
    tokens_output INTEGER,
    processing_time_ms INTEGER,

    -- Confidence and quality
    confidence_score DECIMAL(3,2),      -- 0.00 to 1.00
    hallucination_flags JSONB DEFAULT '[]',  -- Any detected issues

    -- Status
    status VARCHAR(50) DEFAULT 'completed'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'reviewed')),
    error_message TEXT,

    -- Metadata
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewed_by VARCHAR(255),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for analytics_insights
CREATE INDEX IF NOT EXISTS idx_insights_date_range ON analytics_insights(date_from, date_to);
CREATE INDEX IF NOT EXISTS idx_insights_type ON analytics_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_insights_status ON analytics_insights(status);
CREATE INDEX IF NOT EXISTS idx_insights_generated ON analytics_insights(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_insights_model ON analytics_insights(model_used);

-- ============================================================================
-- PART 3: LLM PROCESSING QUEUE (for async LLM calls)
-- ============================================================================

CREATE TABLE IF NOT EXISTS llm_processing_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Task definition
    task_type VARCHAR(50) NOT NULL
        CHECK (task_type IN ('normalization', 'feature_engineering', 'analysis', 'custom')),
    layer VARCHAR(10) NOT NULL
        CHECK (layer IN ('L2', 'L3', 'L4')),

    -- Input data reference
    input_type VARCHAR(50) NOT NULL,    -- "raw_events", "normalized_events", "feature_store"
    input_ids JSONB NOT NULL,           -- Array of IDs to process

    -- Processing config
    model_preference VARCHAR(100),       -- Preferred model
    prompt_template VARCHAR(100),        -- Which prompt to use
    priority INTEGER DEFAULT 5,          -- 1=highest, 10=lowest

    -- Status tracking
    status VARCHAR(50) DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,

    -- Results
    output_type VARCHAR(50),            -- "normalized_events", "feature_store", "analytics_insights"
    output_ids JSONB,                   -- Array of created record IDs

    -- Error handling
    error_message TEXT,
    error_details JSONB,

    -- Timing
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for llm_processing_queue
CREATE INDEX IF NOT EXISTS idx_llm_queue_status ON llm_processing_queue(status);
CREATE INDEX IF NOT EXISTS idx_llm_queue_priority ON llm_processing_queue(priority, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_llm_queue_task_type ON llm_processing_queue(task_type);
CREATE INDEX IF NOT EXISTS idx_llm_queue_layer ON llm_processing_queue(layer);

-- ============================================================================
-- PART 4: TRIGGERS
-- ============================================================================

-- Function for automatic updated_at column update
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP;
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for updated_at on unified_metrics
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_unified_metrics_updated_at') THEN
        CREATE TRIGGER update_unified_metrics_updated_at
        BEFORE UPDATE ON unified_metrics
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- ============================================================================
-- PART 5: VIEWS
-- ============================================================================

-- Daily unified summary view
CREATE OR REPLACE VIEW daily_unified_summary AS
SELECT
    date,
    unified_sessions,
    unified_users,
    unified_pageviews,
    engagement_rate,
    bounce_rate,
    avg_hot_score,
    dominant_segment,
    CASE
        WHEN ga4_data_available AND metrika_data_available THEN 'both'
        WHEN ga4_data_available THEN 'ga4_only'
        WHEN metrika_data_available THEN 'metrika_only'
        ELSE 'none'
    END as data_sources
FROM unified_metrics
ORDER BY date DESC;

-- Latest insights view
CREATE OR REPLACE VIEW latest_insights AS
SELECT
    id,
    date_from,
    date_to,
    insight_type,
    executive_summary,
    model_used,
    confidence_score,
    generated_at
FROM analytics_insights
WHERE status = 'completed'
ORDER BY generated_at DESC
LIMIT 10;

-- ============================================================================
-- PART 6: COMMENTS
-- ============================================================================

COMMENT ON TABLE unified_metrics IS 'Daily unified metrics from GA4 + Yandex Metrika';
COMMENT ON TABLE analytics_insights IS 'AI-generated analytics insights (L4 layer)';
COMMENT ON TABLE llm_processing_queue IS 'Queue for async LLM processing tasks';

-- ============================================================================
-- DONE
-- ============================================================================
