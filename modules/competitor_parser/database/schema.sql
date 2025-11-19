-- =========================================
-- Competitor Parser Module - Database Schema
-- =========================================
-- Схема для хранения результатов парсинга конкурентов
-- С заделами для будущих модулей (SEO, Content Gen, PBN)

-- =========================================
-- 1. Parser Tasks Table
-- =========================================
CREATE TABLE IF NOT EXISTS parser_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT NOT NULL,
    parser_type VARCHAR(50) NOT NULL DEFAULT 'universal',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    
    -- Results
    products_found INTEGER DEFAULT 0,
    products_saved INTEGER DEFAULT 0,
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Settings
    max_pages INTEGER DEFAULT 1,
    rate_limit DECIMAL(5, 2) DEFAULT 2.0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    CONSTRAINT valid_parser_type CHECK (parser_type IN ('universal', 'satu', 'kaspi', 'custom'))
);

CREATE INDEX IF NOT EXISTS idx_parser_tasks_status ON parser_tasks(status);
CREATE INDEX IF NOT EXISTS idx_parser_tasks_created_at ON parser_tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_parser_tasks_parser_type ON parser_tasks(parser_type);

-- =========================================
-- 2. Parsed Products Table
-- =========================================
CREATE TABLE IF NOT EXISTS parsed_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES parser_tasks(id) ON DELETE CASCADE,
    
    -- Basic Product Info
    sku VARCHAR(255),
    external_id VARCHAR(255),
    title TEXT NOT NULL,
    description TEXT,
    short_description TEXT,
    
    -- Price Info
    price_amount DECIMAL(10, 2),
    price_currency VARCHAR(10) DEFAULT 'KZT',
    old_price DECIMAL(10, 2),
    discount_percent DECIMAL(5, 2),
    
    -- Classification
    category TEXT,
    breadcrumbs JSONB DEFAULT '[]',
    brand VARCHAR(255),
    manufacturer VARCHAR(255),
    
    -- Stock & Rating
    stock_status VARCHAR(50),
    in_stock BOOLEAN,
    rating DECIMAL(3, 2),
    reviews_count INTEGER,
    
    -- Attributes & Images (JSON)
    attributes JSONB DEFAULT '[]',
    images JSONB DEFAULT '[]',
    
    -- SEO Data (JSON) - для будущего SEO Analyzer
    seo_data JSONB DEFAULT '{}',
    
    -- Source Info
    source_url TEXT NOT NULL,
    source_site VARCHAR(255) NOT NULL,
    parser_type VARCHAR(50) DEFAULT 'universal',
    
    -- Metadata
    parsed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    parser_version VARCHAR(20) DEFAULT '0.1.0',
    
    -- Optional: Raw HTML for debugging
    raw_html TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(source_url, parsed_at)
);

-- Indexes для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_parsed_products_source_site ON parsed_products(source_site);
CREATE INDEX IF NOT EXISTS idx_parsed_products_brand ON parsed_products(brand);
CREATE INDEX IF NOT EXISTS idx_parsed_products_category ON parsed_products(category);
CREATE INDEX IF NOT EXISTS idx_parsed_products_task_id ON parsed_products(task_id);
CREATE INDEX IF NOT EXISTS idx_parsed_products_parsed_at ON parsed_products(parsed_at DESC);
CREATE INDEX IF NOT EXISTS idx_parsed_products_sku ON parsed_products(sku);

-- GIN index для JSONB полей (быстрый поиск в JSON)
CREATE INDEX IF NOT EXISTS idx_parsed_products_attributes_gin ON parsed_products USING GIN (attributes);
CREATE INDEX IF NOT EXISTS idx_parsed_products_seo_data_gin ON parsed_products USING GIN (seo_data);

-- =========================================
-- 3. Parsed Sites Table (для экспорта)
-- =========================================
CREATE TABLE IF NOT EXISTS parsed_sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_domain VARCHAR(255) UNIQUE NOT NULL,
    site_name VARCHAR(255),
    
    -- Statistics
    total_products INTEGER DEFAULT 0,
    last_parsed_at TIMESTAMP WITH TIME ZONE,
    
    -- Parser Config (JSON)
    parser_config JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_parsed_sites_domain ON parsed_sites(site_domain);

-- =========================================
-- ЗАДЕЛЫ ДЛЯ БУДУЩИХ МОДУЛЕЙ
-- =========================================
-- Эти таблицы создадим в следующих итерациях

-- =========================================
-- Итерация 2: SEO Analyzer Module
-- =========================================
-- CREATE TABLE IF NOT EXISTS seo_reports (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     product_id UUID REFERENCES parsed_products(id) ON DELETE CASCADE,
--     url TEXT NOT NULL,
--     
--     -- SEO Metrics
--     title_length INTEGER,
--     description_length INTEGER,
--     h1_count INTEGER,
--     h2_count INTEGER,
--     internal_links_count INTEGER,
--     external_links_count INTEGER,
--     images_without_alt INTEGER,
--     
--     -- Content Analysis
--     word_count INTEGER,
--     keyword_density JSONB,
--     lsi_keywords JSONB,
--     
--     -- Technical SEO
--     has_canonical BOOLEAN,
--     has_schema_org BOOLEAN,
--     page_load_time DECIMAL(5, 2),
--     
--     -- Score
--     seo_score INTEGER CHECK (seo_score >= 0 AND seo_score <= 100),
--     
--     -- Full Report (JSON)
--     full_report JSONB,
--     
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- );

-- =========================================
-- Итерация 3: Content Generator Module
-- =========================================
-- CREATE TABLE IF NOT EXISTS generated_content (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     product_id UUID REFERENCES parsed_products(id) ON DELETE CASCADE,
--     
--     -- Generated Content
--     generated_title TEXT,
--     generated_description TEXT,
--     generated_short_description TEXT,
--     
--     -- SEO Optimized
--     seo_title TEXT,
--     seo_description TEXT,
--     seo_keywords JSONB,
--     
--     -- Spintax versions
--     spintax_variants JSONB,
--     
--     -- AI Model Info
--     ai_model VARCHAR(100),
--     ai_prompt TEXT,
--     
--     -- Quality Score
--     uniqueness_score DECIMAL(5, 2),
--     readability_score DECIMAL(5, 2),
--     
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- );

-- =========================================
-- Итерация 4: PBN Manager Module
-- =========================================
-- CREATE TABLE IF NOT EXISTS pbn_sites (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     domain VARCHAR(255) UNIQUE NOT NULL,
--     
--     -- WordPress Credentials
--     wp_url TEXT NOT NULL,
--     wp_username VARCHAR(255),
--     wp_password_encrypted TEXT,
--     wp_api_key TEXT,
--     
--     -- Site Info
--     ip_address VARCHAR(45),
--     hosting_provider VARCHAR(255),
--     
--     -- Status
--     is_active BOOLEAN DEFAULT true,
--     last_post_at TIMESTAMP WITH TIME ZONE,
--     
--     -- Stats
--     total_posts INTEGER DEFAULT 0,
--     
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
--     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- );

-- CREATE TABLE IF NOT EXISTS pbn_posts (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     pbn_site_id UUID REFERENCES pbn_sites(id) ON DELETE CASCADE,
--     content_id UUID REFERENCES generated_content(id),
--     
--     -- WordPress Post Info
--     wp_post_id INTEGER,
--     wp_post_url TEXT,
--     
--     -- Post Content
--     title TEXT NOT NULL,
--     content TEXT NOT NULL,
--     
--     -- Links
--     outbound_links JSONB DEFAULT '[]',
--     anchor_texts JSONB DEFAULT '[]',
--     
--     -- Status
--     post_status VARCHAR(50) DEFAULT 'draft',
--     is_indexed BOOLEAN DEFAULT false,
--     
--     -- Timestamps
--     published_at TIMESTAMP WITH TIME ZONE,
--     indexed_at TIMESTAMP WITH TIME ZONE,
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- );

-- =========================================
-- Итерация 5: Money Site Manager & Link Network
-- =========================================
-- CREATE TABLE IF NOT EXISTS money_sites (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     domain VARCHAR(255) UNIQUE NOT NULL,
--     cms_type VARCHAR(50),
--     
--     -- Integration
--     api_url TEXT,
--     api_key TEXT,
--     
--     -- Stats
--     total_products INTEGER DEFAULT 0,
--     
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- );

-- CREATE TABLE IF NOT EXISTS link_network (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     from_site_id UUID,  -- PBN site or Money site
--     to_site_id UUID,    -- Usually Money site
--     
--     -- Link Details
--     anchor_text TEXT,
--     link_url TEXT NOT NULL,
--     link_type VARCHAR(50),
--     
--     -- Context
--     post_id UUID,
--     
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- );

-- =========================================
-- Функции и триггеры
-- =========================================

-- Функция для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для parsed_products
DROP TRIGGER IF EXISTS update_parsed_products_updated_at ON parsed_products;
CREATE TRIGGER update_parsed_products_updated_at
    BEFORE UPDATE ON parsed_products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Триггер для parsed_sites
DROP TRIGGER IF EXISTS update_parsed_sites_updated_at ON parsed_sites;
CREATE TRIGGER update_parsed_sites_updated_at
    BEFORE UPDATE ON parsed_sites
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =========================================
-- Views для аналитики
-- =========================================

-- Статистика по сайтам
CREATE OR REPLACE VIEW v_site_statistics AS
SELECT 
    source_site,
    COUNT(*) as total_products,
    COUNT(DISTINCT task_id) as total_tasks,
    AVG(price_amount) as avg_price,
    MAX(parsed_at) as last_parsed_at
FROM parsed_products
GROUP BY source_site;

-- Последние задачи парсинга
CREATE OR REPLACE VIEW v_recent_parser_tasks AS
SELECT 
    t.id,
    t.url,
    t.parser_type,
    t.status,
    t.progress,
    t.products_found,
    t.created_at,
    t.completed_at,
    COUNT(p.id) as actual_products_count
FROM parser_tasks t
LEFT JOIN parsed_products p ON p.task_id = t.id
GROUP BY t.id
ORDER BY t.created_at DESC
LIMIT 100;

-- =========================================
-- Комментарии для документации
-- =========================================
COMMENT ON TABLE parser_tasks IS 'Задачи парсинга сайтов конкурентов';
COMMENT ON TABLE parsed_products IS 'Распарсенные товары с SEO метаданными';
COMMENT ON TABLE parsed_sites IS 'Список распарсенных сайтов';

COMMENT ON COLUMN parsed_products.seo_data IS 'SEO метаданные (meta tags, H1-H6, canonical) для SEO Analyzer';
COMMENT ON COLUMN parsed_products.attributes IS 'Характеристики товара в формате JSON';
COMMENT ON COLUMN parsed_products.images IS 'Изображения товара в формате JSON';

