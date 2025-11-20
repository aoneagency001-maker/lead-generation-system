-- ===================================
-- TELEGRAM BOTS SUBSCRIBERS
-- ===================================
-- Таблица для хранения подписчиков Telegram ботов
-- Автоматически сохраняет chat_id когда пользователь нажимает /start

CREATE TABLE IF NOT EXISTS telegram_bot_subscribers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Идентификация бота
    bot_type VARCHAR(50) NOT NULL, -- monitor, leads, sales, qualification и т.д.
    bot_token_hash VARCHAR(255), -- Хэш токена для идентификации (опционально)
    
    -- Данные пользователя Telegram
    chat_id BIGINT NOT NULL, -- Telegram Chat ID
    username TEXT, -- @username (если есть)
    first_name TEXT, -- Имя пользователя
    last_name TEXT, -- Фамилия пользователя
    language_code VARCHAR(10), -- ru, en, kk и т.д.
    
    -- Статус подписки
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'blocked', 'unsubscribed', 'banned')),
    
    -- Метаданные
    metadata JSONB DEFAULT '{}'::JSONB, -- Дополнительные данные
    notes TEXT, -- Заметки администратора
    
    -- Timestamps
    subscribed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    unsubscribed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Уникальность: один chat_id может быть подписан на один тип бота только один раз
    CONSTRAINT telegram_bot_subscribers_bot_chat_unique UNIQUE (bot_type, chat_id)
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_telegram_bot_subscribers_bot_type ON telegram_bot_subscribers(bot_type);
CREATE INDEX IF NOT EXISTS idx_telegram_bot_subscribers_chat_id ON telegram_bot_subscribers(chat_id);
CREATE INDEX IF NOT EXISTS idx_telegram_bot_subscribers_status ON telegram_bot_subscribers(status);
CREATE INDEX IF NOT EXISTS idx_telegram_bot_subscribers_subscribed_at ON telegram_bot_subscribers(subscribed_at DESC);

-- Триггер для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_telegram_bot_subscribers_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_telegram_bot_subscribers_updated_at
    BEFORE UPDATE ON telegram_bot_subscribers
    FOR EACH ROW
    EXECUTE FUNCTION update_telegram_bot_subscribers_updated_at();

-- Триггер для обновления last_activity_at при любой активности
CREATE OR REPLACE FUNCTION update_telegram_bot_subscribers_activity()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_activity_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_telegram_bot_subscribers_activity
    BEFORE UPDATE ON telegram_bot_subscribers
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status OR OLD.metadata IS DISTINCT FROM NEW.metadata)
    EXECUTE FUNCTION update_telegram_bot_subscribers_activity();

-- Комментарии
COMMENT ON TABLE telegram_bot_subscribers IS 'Подписчики Telegram ботов системы';
COMMENT ON COLUMN telegram_bot_subscribers.bot_type IS 'Тип бота: monitor, leads, sales, qualification и т.д.';
COMMENT ON COLUMN telegram_bot_subscribers.chat_id IS 'Telegram Chat ID пользователя';
COMMENT ON COLUMN telegram_bot_subscribers.status IS 'Статус подписки: active, blocked, unsubscribed, banned';

