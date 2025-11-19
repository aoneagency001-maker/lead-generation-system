-- ===================================
-- Platform Modules Table
-- Таблица для управления модулями платформ
-- ===================================

CREATE TABLE IF NOT EXISTS platform_modules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Основная информация
    name VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL, -- olx, satu, kaspi, etc.
    status VARCHAR(50) NOT NULL DEFAULT 'inactive', -- active, testing, inactive, archived
    pipeline_stage VARCHAR(50) NOT NULL DEFAULT 'research', -- research, acquisition, processing, conversion, analytics

    -- Описание
    description TEXT,
    version VARCHAR(50) DEFAULT '1.0.0',

    -- API конфигурация
    api_url VARCHAR(255) NOT NULL, -- http://localhost:8001
    health_endpoint VARCHAR(255) DEFAULT '/health',

    -- Функциональность
    features JSONB DEFAULT '[]'::jsonb, -- Список доступных функций
    config JSONB DEFAULT '{}'::jsonb, -- Конфигурация модуля

    -- Здоровье
    last_health_check TIMESTAMPTZ,
    is_healthy BOOLEAN DEFAULT false,

    -- Порядок отображения
    "order" INTEGER DEFAULT 0,
    pipeline_order INTEGER DEFAULT 0,

    -- Constraints
    CONSTRAINT platform_modules_platform_check CHECK (platform IN ('olx', 'satu', 'kaspi', 'telegram', 'whatsapp')),
    CONSTRAINT platform_modules_status_check CHECK (status IN ('active', 'testing', 'inactive', 'archived')),
    CONSTRAINT platform_modules_pipeline_stage_check CHECK (pipeline_stage IN ('research', 'acquisition', 'processing', 'conversion', 'analytics'))
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_platform_modules_status ON platform_modules(status);
CREATE INDEX IF NOT EXISTS idx_platform_modules_platform ON platform_modules(platform);
CREATE INDEX IF NOT EXISTS idx_platform_modules_pipeline_stage ON platform_modules(pipeline_stage);
CREATE INDEX IF NOT EXISTS idx_platform_modules_order ON platform_modules("order");
CREATE INDEX IF NOT EXISTS idx_platform_modules_pipeline_order ON platform_modules(pipeline_order);

-- Триггер для автообновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_platform_modules_updated_at
    BEFORE UPDATE ON platform_modules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Вставка тестовых данных (OLX и Satu модули)
INSERT INTO platform_modules (name, platform, status, pipeline_stage, description, version, api_url, features, "order", pipeline_order, is_healthy)
VALUES
    (
        'OLX Module',
        'olx',
        'testing',
        'acquisition',
        'Модуль для работы с платформой OLX.kz - парсинг объявлений, публикация, OAuth авторизация',
        '1.0.0',
        'http://localhost:8001',
        '["OAuth 2.0", "Парсинг (3 метода)", "Публикация объявлений", "SDK"]'::jsonb,
        0,
        0,
        false
    ),
    (
        'Satu Module',
        'satu',
        'testing',
        'acquisition',
        'Модуль для работы с платформой Satu.kz - парсинг товаров, публикация, API Token авторизация',
        '1.0.0',
        'http://localhost:8002',
        '["API Token Auth", "Парсинг (2 метода)", "Публикация товаров", "SDK"]'::jsonb,
        1,
        1,
        false
    )
ON CONFLICT DO NOTHING;

-- Комментарии к таблице
COMMENT ON TABLE platform_modules IS 'Модули платформ для управления интеграциями';
COMMENT ON COLUMN platform_modules.status IS 'Статус модуля: active (активен), testing (тестируется), inactive (неактивен), archived (в архиве)';
COMMENT ON COLUMN platform_modules.pipeline_stage IS 'Стратегический этап: research (анализ), acquisition (привлечение), processing (обработка), conversion (конверсия), analytics (аналитика)';
COMMENT ON COLUMN platform_modules.features IS 'JSON массив доступных функций модуля';
COMMENT ON COLUMN platform_modules.config IS 'JSON объект с конфигурацией модуля';
COMMENT ON COLUMN platform_modules."order" IS 'Порядок отображения модуля в статусном Kanban';
COMMENT ON COLUMN platform_modules.pipeline_order IS 'Порядок отображения модуля в стратегическом Kanban';
