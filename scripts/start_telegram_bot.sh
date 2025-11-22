#!/bin/bash
# Скрипт для запуска Telegram бота

echo "🤖 Starting Telegram Bot..."

# Проверка .env
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please create .env file with TELEGRAM_MONITOR_BOT_TOKEN and TELEGRAM_MONITOR_CHAT_ID"
    exit 1
fi

# Проверка переменных (с fallback на старые имена)
source .env
TELEGRAM_BOT_TOKEN="${TELEGRAM_MONITOR_BOT_TOKEN:-$TELEGRAM_BOT_TOKEN}"
TELEGRAM_CHAT_ID="${TELEGRAM_MONITOR_CHAT_ID:-${TELEGRAM_NOTIFICATION_CHAT_ID:-$TELEGRAM_CHAT_ID}}"

if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "❌ Error: TELEGRAM_MONITOR_BOT_TOKEN (or TELEGRAM_BOT_TOKEN) or"
    echo "          TELEGRAM_MONITOR_CHAT_ID (or TELEGRAM_NOTIFICATION_CHAT_ID) not set in .env"
    exit 1
fi

echo "✅ Configuration found"
echo "🚀 Starting bot..."

# Запуск бота
python -m shared.telegram_bot

