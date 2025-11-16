-- ===================================
-- LEAD GENERATION SYSTEM DATABASE SCHEMA
-- ===================================
-- Для Supabase PostgreSQL
-- Запустите этот скрипт через scripts/setup_database.py

-- ===================================
-- 1. NICHES (Ниши для тестирования)
-- ===================================
CREATE TABLE IF NOT EXISTS niches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    status VARCHAR(50) DEFAULT 'research' CHECK (status IN ('research', 'active', 'paused', 'completed', 'rejected')),
    
    -- Целевые метрики
    cpl_target DECIMAL(10, 2), -- Cost Per Lead (целевая стоимость лида)
    roi_target DECIMAL(10, 2), -- ROI target (целевой ROI)
    
    -- Анализ рынка
    market_size INTEGER,
    competition_level VARCHAR(50), -- low, medium, high
    avg_price DECIMAL(10, 2),
    seasonality JSONB, -- {winter: true, summer: false, ...}
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Индексы для niches
CREATE INDEX IF NOT EXISTS idx_niches_status ON niches(status);
CREATE INDEX IF NOT EXISTS idx_niches_created_at ON niches(created_at DESC);

-- ===================================
-- 2. CAMPAIGNS (Кампании по нишам)
-- ===================================
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    niche_id UUID NOT NULL REFERENCES niches(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL, -- olx, kaspi, telegram
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'completed', 'failed')),
    
    -- Бюджет и сроки
    budget DECIMAL(10, 2),
    spent DECIMAL(10, 2) DEFAULT 0,
    start_date DATE,
    end_date DATE,
    
    -- Конфигурация
    config JSONB, -- Настройки кампании (прокси, частота постинга и т.д.)
    
    -- Метрики
    ads_count INTEGER DEFAULT 0,
    leads_count INTEGER DEFAULT 0,
    conversions_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для campaigns
CREATE INDEX IF NOT EXISTS idx_campaigns_niche ON campaigns(niche_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_platform ON campaigns(platform);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);

-- ===================================
-- 3. ADS (Объявления)
-- ===================================
CREATE TABLE IF NOT EXISTS ads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    
    platform VARCHAR(50) NOT NULL, -- olx, kaspi, telegram
    external_id VARCHAR(255), -- ID на внешней платформе
    url TEXT,
    
    -- Контент объявления
    title VARCHAR(500) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2),
    images JSONB, -- Массив URL изображений
    
    -- Статус
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'active', 'expired', 'banned', 'deleted')),
    
    -- Метрики
    views_count INTEGER DEFAULT 0,
    clicks_count INTEGER DEFAULT 0,
    messages_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для ads
CREATE INDEX IF NOT EXISTS idx_ads_campaign ON ads(campaign_id);
CREATE INDEX IF NOT EXISTS idx_ads_platform ON ads(platform);
CREATE INDEX IF NOT EXISTS idx_ads_status ON ads(status);
CREATE INDEX IF NOT EXISTS idx_ads_published_at ON ads(published_at DESC);

-- ===================================
-- 4. LEADS (Лиды)
-- ===================================
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_id UUID REFERENCES ads(id) ON DELETE SET NULL,
    
    -- Контактная информация
    name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    
    -- Источник
    source VARCHAR(50) NOT NULL, -- whatsapp, telegram, olx, kaspi
    platform_user_id VARCHAR(255), -- ID пользователя в мессенджере
    
    -- Статус и квалификация
    status VARCHAR(50) DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'qualified', 'hot', 'won', 'lost', 'spam')),
    quality_score INTEGER CHECK (quality_score BETWEEN 0 AND 100), -- 0-100
    
    -- Дополнительная информация
    budget DECIMAL(10, 2),
    urgency VARCHAR(50), -- immediate, week, month, flexible
    notes TEXT,
    metadata JSONB, -- Дополнительные данные из квалификации
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    contacted_at TIMESTAMP WITH TIME ZONE,
    qualified_at TIMESTAMP WITH TIME ZONE,
    closed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для leads
CREATE INDEX IF NOT EXISTS idx_leads_ad ON leads(ad_id);
CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone);

-- ===================================
-- 5. CONVERSATIONS (Сообщения с лидами)
-- ===================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    
    platform VARCHAR(50) NOT NULL, -- whatsapp, telegram
    
    -- Сообщение
    message TEXT NOT NULL,
    sender VARCHAR(50) NOT NULL CHECK (sender IN ('bot', 'lead', 'human')), -- кто отправил
    
    -- Метаданные
    message_type VARCHAR(50) DEFAULT 'text', -- text, image, document, location
    metadata JSONB, -- Дополнительные данные (вложения и т.д.)
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для conversations
CREATE INDEX IF NOT EXISTS idx_conversations_lead ON conversations(lead_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);

-- ===================================
-- 6. MARKET_RESEARCH (Результаты исследования)
-- ===================================
CREATE TABLE IF NOT EXISTS market_research (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    niche_id UUID REFERENCES niches(id) ON DELETE CASCADE,
    
    platform VARCHAR(50) NOT NULL, -- olx, kaspi, google_trends
    
    -- Данные исследования
    data JSONB NOT NULL, -- Сырые данные парсинга
    analysis JSONB, -- Результаты анализа
    
    -- Метрики
    ads_count INTEGER,
    avg_price DECIMAL(10, 2),
    min_price DECIMAL(10, 2),
    max_price DECIMAL(10, 2),
    competition_score INTEGER CHECK (competition_score BETWEEN 0 AND 100),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для market_research
CREATE INDEX IF NOT EXISTS idx_research_niche ON market_research(niche_id);
CREATE INDEX IF NOT EXISTS idx_research_platform ON market_research(platform);

-- ===================================
-- TRIGGERS для автоматического обновления updated_at
-- ===================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP;
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Применяем триггеры
CREATE TRIGGER update_niches_updated_at BEFORE UPDATE ON niches
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ads_updated_at BEFORE UPDATE ON ads
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===================================
-- VIEWS для удобного доступа к данным
-- ===================================

-- Общий вид кампаний с метриками
CREATE OR REPLACE VIEW campaigns_summary AS
SELECT 
    c.id,
    c.name,
    c.platform,
    c.status,
    n.name as niche_name,
    c.budget,
    c.spent,
    c.ads_count,
    c.leads_count,
    c.conversions_count,
    CASE 
        WHEN c.spent > 0 THEN ROUND(c.spent::numeric / NULLIF(c.leads_count, 0), 2)
        ELSE NULL 
    END as cpl, -- Cost Per Lead
    CASE 
        WHEN c.spent > 0 AND c.conversions_count > 0 
        THEN ROUND((c.conversions_count * n.avg_price - c.spent) / c.spent * 100, 2)
        ELSE NULL 
    END as roi,
    c.created_at,
    c.updated_at
FROM campaigns c
JOIN niches n ON c.niche_id = n.id;

-- Комментарии к таблицам
COMMENT ON TABLE niches IS 'Ниши для тестирования (вертикали бизнеса)';
COMMENT ON TABLE campaigns IS 'Маркетинговые кампании по нишам';
COMMENT ON TABLE ads IS 'Объявления на различных платформах';
COMMENT ON TABLE leads IS 'Лиды (потенциальные клиенты)';
COMMENT ON TABLE conversations IS 'История общения с лидами через боты';
COMMENT ON TABLE market_research IS 'Результаты исследования рынка';

-- ===================================
-- Row Level Security (RLS) - опционально
-- ===================================
-- Раскомментируйте если нужна многопользовательская система

-- ALTER TABLE niches ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE ads ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Политики доступа (примеры)
-- CREATE POLICY "Enable read access for all users" ON niches FOR SELECT USING (true);
-- CREATE POLICY "Enable insert for authenticated users only" ON niches FOR INSERT WITH CHECK (auth.role() = 'authenticated');

