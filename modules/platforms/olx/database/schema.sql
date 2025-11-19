-- =========================================
-- OLX Module Database Schema
-- =========================================
-- Автономные таблицы для OLX модуля
-- Префикс: olx_*

-- Enable UUID extension if not already enabled
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =========================================
-- Аккаунты OLX
-- =========================================
CREATE TABLE IF NOT EXISTS olx_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    password_hash TEXT,  -- зашифрованный пароль (не храним в открытом виде)
    
    -- OAuth tokens (для официального API)
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,
    client_id TEXT,  -- OLX API Client ID
    
    -- Browser session (для Playwright авторизации)
    cookies JSONB,  -- сохраненные cookies сессии
    user_agent TEXT,  -- User-Agent привязанный к аккаунту
    proxy_url TEXT,  -- Прокси привязанный к аккаунту
    
    -- Метаданные
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'banned', 'suspended', 'expired')),
    last_login_at TIMESTAMPTZ,
    login_method TEXT DEFAULT 'oauth' CHECK (login_method IN ('oauth', 'browser')),
    
    -- Аудит
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Индексы
    CONSTRAINT olx_accounts_email_key UNIQUE (email)
);

CREATE INDEX IF NOT EXISTS idx_olx_accounts_status ON olx_accounts(status);
CREATE INDEX IF NOT EXISTS idx_olx_accounts_email ON olx_accounts(email);

-- =========================================
-- Объявления OLX
-- =========================================
CREATE TABLE IF NOT EXISTS olx_ads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES olx_accounts(id) ON DELETE CASCADE,
    
    -- OLX данные
    external_id TEXT,  -- ID объявления на olx.kz
    url TEXT,  -- Прямая ссылка на объявление
    
    -- Содержимое
    title TEXT NOT NULL,
    description TEXT,
    price NUMERIC(12, 2),
    currency TEXT DEFAULT 'KZT',
    
    -- Категория и локация
    category TEXT,
    category_id TEXT,
    city TEXT,
    region TEXT,
    
    -- Медиа
    images JSONB DEFAULT '[]'::JSONB,  -- Массив URL изображений
    
    -- Статусы
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'active', 'expired', 'deleted', 'moderation')),
    publish_method TEXT CHECK (publish_method IN ('api', 'browser')),
    
    -- Статистика
    views_count INTEGER DEFAULT 0,
    favorites_count INTEGER DEFAULT 0,
    messages_count INTEGER DEFAULT 0,
    
    -- Временные метки
    published_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Метаданные
    metadata JSONB DEFAULT '{}'::JSONB  -- Дополнительные данные
);

CREATE INDEX IF NOT EXISTS idx_olx_ads_account_id ON olx_ads(account_id);
CREATE INDEX IF NOT EXISTS idx_olx_ads_external_id ON olx_ads(external_id);
CREATE INDEX IF NOT EXISTS idx_olx_ads_status ON olx_ads(status);
CREATE INDEX IF NOT EXISTS idx_olx_ads_published_at ON olx_ads(published_at DESC);

-- =========================================
-- Парсинг результаты OLX
-- =========================================
CREATE TABLE IF NOT EXISTS olx_parsed_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Параметры парсинга
    search_query TEXT,
    search_url TEXT,
    city TEXT,
    category TEXT,
    parser_method TEXT CHECK (parser_method IN ('lerdem', 'playwright', 'api')),
    
    -- Результаты
    data JSONB NOT NULL,  -- Массив найденных объявлений
    items_count INTEGER DEFAULT 0,
    
    -- Метаданные парсинга
    parse_duration_seconds NUMERIC(10, 2),
    pages_parsed INTEGER DEFAULT 1,
    
    -- Временные метки
    parsed_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ошибки
    errors JSONB DEFAULT '[]'::JSONB,
    status TEXT DEFAULT 'success' CHECK (status IN ('success', 'partial', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_olx_parsed_data_parsed_at ON olx_parsed_data(parsed_at DESC);
CREATE INDEX IF NOT EXISTS idx_olx_parsed_data_search_query ON olx_parsed_data(search_query);

-- =========================================
-- Парсинг задачи (для асинхронной обработки)
-- =========================================
CREATE TABLE IF NOT EXISTS olx_parser_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Параметры
    search_query TEXT NOT NULL,
    city TEXT,
    category TEXT,
    parser_method TEXT NOT NULL,
    
    -- Статус
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    progress INTEGER DEFAULT 0,  -- 0-100
    
    -- Результат
    result_id UUID REFERENCES olx_parsed_data(id),
    error_message TEXT,
    
    -- Временные метки
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_olx_parser_tasks_status ON olx_parser_tasks(status);
CREATE INDEX IF NOT EXISTS idx_olx_parser_tasks_created_at ON olx_parser_tasks(created_at DESC);

-- =========================================
-- Триггеры для updated_at
-- =========================================

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_olx_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для olx_accounts
DROP TRIGGER IF EXISTS update_olx_accounts_updated_at ON olx_accounts;
CREATE TRIGGER update_olx_accounts_updated_at
    BEFORE UPDATE ON olx_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_olx_updated_at_column();

-- Триггер для olx_ads
DROP TRIGGER IF EXISTS update_olx_ads_updated_at ON olx_ads;
CREATE TRIGGER update_olx_ads_updated_at
    BEFORE UPDATE ON olx_ads
    FOR EACH ROW
    EXECUTE FUNCTION update_olx_updated_at_column();

-- =========================================
-- Комментарии к таблицам
-- =========================================

COMMENT ON TABLE olx_accounts IS 'Аккаунты OLX для авторизации (OAuth и Browser)';
COMMENT ON TABLE olx_ads IS 'Объявления опубликованные на OLX';
COMMENT ON TABLE olx_parsed_data IS 'Результаты парсинга OLX';
COMMENT ON TABLE olx_parser_tasks IS 'Задачи парсинга для асинхронной обработки';

COMMENT ON COLUMN olx_accounts.cookies IS 'JSONB с cookies сессии для Playwright';
COMMENT ON COLUMN olx_accounts.access_token IS 'OAuth 2.0 access token';
COMMENT ON COLUMN olx_ads.external_id IS 'ID объявления на olx.kz';
COMMENT ON COLUMN olx_parsed_data.data IS 'JSONB массив с найденными объявлениями';


