-- =========================================
-- Satu.kz Module Database Schema
-- =========================================
-- Автономные таблицы для Satu модуля
-- Префикс: satu_*

-- Enable UUID extension if not already enabled
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =========================================
-- Аккаунты Satu.kz
-- =========================================
CREATE TABLE IF NOT EXISTS satu_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Данные компании
    company_name TEXT NOT NULL,
    company_id TEXT,  -- ID компании на satu.kz
    
    -- API токен
    api_token TEXT NOT NULL,
    token_permissions JSONB DEFAULT '{}'::JSONB,  -- Права доступа токена
    token_expires_at TIMESTAMPTZ,
    
    -- Дополнительные данные
    email TEXT,
    phone TEXT,
    
    -- Browser session (для Playwright если API недостаточно)
    cookies JSONB,
    user_agent TEXT,
    proxy_url TEXT,
    
    -- Статус
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'expired', 'suspended')),
    
    -- Аудит
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_api_call_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_satu_accounts_status ON satu_accounts(status);
CREATE INDEX IF NOT EXISTS idx_satu_accounts_company_name ON satu_accounts(company_name);

-- =========================================
-- Товары на Satu.kz
-- =========================================
CREATE TABLE IF NOT EXISTS satu_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES satu_accounts(id) ON DELETE CASCADE,
    
    -- Satu данные
    external_id TEXT,  -- ID товара на satu.kz
    url TEXT,  -- Прямая ссылка
    
    -- Содержимое
    title TEXT NOT NULL,
    description TEXT,
    price NUMERIC(12, 2),
    currency TEXT DEFAULT 'KZT',
    
    -- Категория
    category TEXT,
    category_id TEXT,
    group_id TEXT,  -- ID группы товаров
    
    -- Характеристики
    attributes JSONB DEFAULT '{}'::JSONB,  -- Характеристики товара
    
    -- Медиа
    images JSONB DEFAULT '[]'::JSONB,
    
    -- Склад
    stock_quantity INTEGER DEFAULT 0,
    sku TEXT,  -- Артикул
    
    -- Статус
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'active', 'inactive', 'deleted')),
    publish_method TEXT CHECK (publish_method IN ('api', 'browser')),
    
    -- Статистика
    views_count INTEGER DEFAULT 0,
    orders_count INTEGER DEFAULT 0,
    
    -- Временные метки
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Метаданные
    metadata JSONB DEFAULT '{}'::JSONB
);

CREATE INDEX IF NOT EXISTS idx_satu_products_account_id ON satu_products(account_id);
CREATE INDEX IF NOT EXISTS idx_satu_products_external_id ON satu_products(external_id);
CREATE INDEX IF NOT EXISTS idx_satu_products_status ON satu_products(status);
CREATE INDEX IF NOT EXISTS idx_satu_products_published_at ON satu_products(published_at DESC);

-- =========================================
-- Заказы с Satu.kz
-- =========================================
CREATE TABLE IF NOT EXISTS satu_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES satu_accounts(id) ON DELETE CASCADE,
    
    -- Satu данные
    external_id TEXT NOT NULL,
    order_number TEXT,
    
    -- Клиент
    customer_name TEXT,
    customer_phone TEXT,
    customer_email TEXT,
    
    -- Заказ
    products JSONB DEFAULT '[]'::JSONB,  -- Список товаров в заказе
    total_amount NUMERIC(12, 2),
    currency TEXT DEFAULT 'KZT',
    
    -- Доставка
    delivery_method TEXT,
    delivery_address TEXT,
    delivery_city TEXT,
    
    -- Статус
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled')),
    payment_status TEXT DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'refunded')),
    
    -- Временные метки
    order_date TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Метаданные
    metadata JSONB DEFAULT '{}'::JSONB
);

CREATE INDEX IF NOT EXISTS idx_satu_orders_account_id ON satu_orders(account_id);
CREATE INDEX IF NOT EXISTS idx_satu_orders_external_id ON satu_orders(external_id);
CREATE INDEX IF NOT EXISTS idx_satu_orders_status ON satu_orders(status);
CREATE INDEX IF NOT EXISTS idx_satu_orders_order_date ON satu_orders(order_date DESC);

-- =========================================
-- Парсинг результаты Satu.kz
-- =========================================
CREATE TABLE IF NOT EXISTS satu_parsed_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Параметры парсинга
    search_query TEXT,
    search_url TEXT,
    category TEXT,
    parser_method TEXT CHECK (parser_method IN ('playwright', 'api')),
    
    -- Результаты
    data JSONB NOT NULL,
    items_count INTEGER DEFAULT 0,
    
    -- Метаданные
    parse_duration_seconds NUMERIC(10, 2),
    pages_parsed INTEGER DEFAULT 1,
    
    -- Временные метки
    parsed_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ошибки
    errors JSONB DEFAULT '[]'::JSONB,
    status TEXT DEFAULT 'success' CHECK (status IN ('success', 'partial', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_satu_parsed_data_parsed_at ON satu_parsed_data(parsed_at DESC);
CREATE INDEX IF NOT EXISTS idx_satu_parsed_data_search_query ON satu_parsed_data(search_query);

-- =========================================
-- Парсинг задачи
-- =========================================
CREATE TABLE IF NOT EXISTS satu_parser_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Параметры
    search_query TEXT NOT NULL,
    category TEXT,
    parser_method TEXT NOT NULL,
    
    -- Статус
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    progress INTEGER DEFAULT 0,
    
    -- Результат
    result_id UUID REFERENCES satu_parsed_data(id),
    error_message TEXT,
    
    -- Временные метки
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_satu_parser_tasks_status ON satu_parser_tasks(status);
CREATE INDEX IF NOT EXISTS idx_satu_parser_tasks_created_at ON satu_parser_tasks(created_at DESC);

-- =========================================
-- Сообщения от клиентов
-- =========================================
CREATE TABLE IF NOT EXISTS satu_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES satu_accounts(id) ON DELETE CASCADE,
    order_id UUID REFERENCES satu_orders(id) ON DELETE SET NULL,
    
    -- Сообщение
    external_id TEXT,
    customer_name TEXT,
    customer_phone TEXT,
    message_text TEXT NOT NULL,
    
    -- Статус
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'read', 'replied', 'archived')),
    replied_at TIMESTAMPTZ,
    
    -- Временные метки
    received_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_satu_messages_account_id ON satu_messages(account_id);
CREATE INDEX IF NOT EXISTS idx_satu_messages_status ON satu_messages(status);
CREATE INDEX IF NOT EXISTS idx_satu_messages_received_at ON satu_messages(received_at DESC);

-- =========================================
-- Триггеры для updated_at
-- =========================================

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_satu_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для satu_accounts
DROP TRIGGER IF EXISTS update_satu_accounts_updated_at ON satu_accounts;
CREATE TRIGGER update_satu_accounts_updated_at
    BEFORE UPDATE ON satu_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_satu_updated_at_column();

-- Триггер для satu_products
DROP TRIGGER IF EXISTS update_satu_products_updated_at ON satu_products;
CREATE TRIGGER update_satu_products_updated_at
    BEFORE UPDATE ON satu_products
    FOR EACH ROW
    EXECUTE FUNCTION update_satu_updated_at_column();

-- Триггер для satu_orders
DROP TRIGGER IF EXISTS update_satu_orders_updated_at ON satu_orders;
CREATE TRIGGER update_satu_orders_updated_at
    BEFORE UPDATE ON satu_orders
    FOR EACH ROW
    EXECUTE FUNCTION update_satu_updated_at_column();

-- =========================================
-- Комментарии к таблицам
-- =========================================

COMMENT ON TABLE satu_accounts IS 'Аккаунты Satu.kz (API токены)';
COMMENT ON TABLE satu_products IS 'Товары опубликованные на Satu.kz';
COMMENT ON TABLE satu_orders IS 'Заказы от клиентов с Satu.kz';
COMMENT ON TABLE satu_parsed_data IS 'Результаты парсинга Satu.kz';
COMMENT ON TABLE satu_parser_tasks IS 'Задачи парсинга для асинхронной обработки';
COMMENT ON TABLE satu_messages IS 'Сообщения от клиентов';

COMMENT ON COLUMN satu_accounts.api_token IS 'API токен для работы с Satu.kz API';
COMMENT ON COLUMN satu_products.external_id IS 'ID товара на satu.kz';
COMMENT ON COLUMN satu_parsed_data.data IS 'JSONB массив с найденными товарами';



