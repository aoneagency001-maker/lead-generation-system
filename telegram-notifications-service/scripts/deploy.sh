#!/bin/bash

# Скрипт для деплоя на AWS
# Использует переменные окружения для AWS credentials

set -e

echo "🚀 Деплой Telegram Notifications Service на AWS..."
echo ""

# Установка переменных окружения
# ⚠️ БЕЗОПАСНОСТЬ: Используем переменные окружения (не хардкод!)
# Убедитесь что AWS_ACCESS_KEY_ID и AWS_SECRET_ACCESS_KEY установлены
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
  echo "❌ Ошибка: AWS_ACCESS_KEY_ID и AWS_SECRET_ACCESS_KEY должны быть установлены"
  echo "   Установите: export AWS_ACCESS_KEY_ID=... && export AWS_SECRET_ACCESS_KEY=..."
  exit 1
fi
export AWS_REGION=eu-central-1

# Проверка сборки
if [ ! -d "dist" ]; then
    echo "📦 Сборка проекта..."
    npm run build
fi

# Деплой
STAGE=${1:-dev}

echo "📤 Деплой в окружение: $STAGE"
echo ""

if [ "$STAGE" = "prod" ]; then
    npm run deploy:prod
else
    npm run deploy:dev
fi

echo ""
echo "✅ Деплой завершён!"
echo ""
echo "📝 Для получения URL endpoint'ов выполните:"
echo "   serverless info --stage $STAGE"
echo ""

