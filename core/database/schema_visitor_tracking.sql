-- ===================================
-- VISITOR TRACKING SCHEMA
-- ===================================
-- Схема для модуля отслеживания посетителей
-- Запустите через Supabase Dashboard → SQL Editor

-- ===================================
-- VISITORS (Посетители сайта)
-- ===================================
CREATE TABLE IF NOT EXISTS visitors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255),
    page TEXT,
    landing_page TEXT,
    referrer TEXT,
    screen_resolution VARCHAR(50),
    ip_address VARCHAR(45), -- IPv6 может быть до 45 символов
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

-- Индексы для visitors
CREATE INDEX IF NOT EXISTS idx_visitors_session_id ON visitors(session_id);
CREATE INDEX IF NOT EXISTS idx_visitors_created_at ON visitors(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_visitors_ip_address ON visitors(ip_address);
CREATE INDEX IF NOT EXISTS idx_visitors_is_bot ON visitors(is_bot);
CREATE INDEX IF NOT EXISTS idx_visitors_device_type ON visitors(device_type);

-- ===================================
-- TILDA WEBHOOKS (Webhook'и от Tilda)
-- ===================================
CREATE TABLE IF NOT EXISTS tilda_webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    
    form_name VARCHAR(255),
    page_url TEXT,
    ip_address VARCHAR(45),
    raw_data JSONB, -- Полные данные из webhook
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для tilda_webhooks
CREATE INDEX IF NOT EXISTS idx_tilda_webhooks_lead_id ON tilda_webhooks(lead_id);
CREATE INDEX IF NOT EXISTS idx_tilda_webhooks_created_at ON tilda_webhooks(created_at DESC);

-- Комментарии к таблицам
COMMENT ON TABLE visitors IS 'Посетители сайта - данные для аналитики';
COMMENT ON TABLE tilda_webhooks IS 'Webhook запросы от Tilda - история заявок с лендингов';

