#!/bin/bash
# Скрипт для запуска Telegram Assistant Bot

echo "🤖 Запуск Telegram Assistant Bot..."

# Проверка переменных окружения
if [ -z "$TELEGRAM_ASSISTANT_BOT_TOKEN" ]; then
    echo "❌ Ошибка: TELEGRAM_ASSISTANT_BOT_TOKEN не установлен"
    echo "💡 Добавь в .env файл: TELEGRAM_ASSISTANT_BOT_TOKEN=твой_токен"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Ошибка: GEMINI_API_KEY не установлен"
    echo "💡 Добавь в .env файл: GEMINI_API_KEY=твой_ключ"
    exit 1
fi

# Запуск бота
python3 -m shared.telegram_assistant_bot


