#!/bin/bash

# Скрипт для деплоя с загрузкой переменных из SSM

set -e

echo "🚀 Деплой Telegram Notifications Service на AWS..."
echo ""

# AWS credentials
# ⚠️ БЕЗОПАСНОСТЬ: Используем переменные окружения (не хардкод!)
# Убедитесь что AWS_ACCESS_KEY_ID и AWS_SECRET_ACCESS_KEY установлены
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
  echo "❌ Ошибка: AWS_ACCESS_KEY_ID и AWS_SECRET_ACCESS_KEY должны быть установлены"
  echo "   Установите: export AWS_ACCESS_KEY_ID=... && export AWS_SECRET_ACCESS_KEY=..."
  exit 1
fi
export AWS_REGION=eu-central-1

# Загружаем переменные из SSM
echo "📥 Загрузка переменных из SSM..."

# Используем Node.js для загрузки из SSM
TELEGRAM_BOT_TOKEN=$(node -e "
const {SSMClient, GetParameterCommand} = require('@aws-sdk/client-ssm');
const client = new SSMClient({region:'eu-central-1', credentials:{accessKeyId:process.env.AWS_ACCESS_KEY_ID, secretAccessKey:process.env.AWS_SECRET_ACCESS_KEY}});
client.send(new GetParameterCommand({Name:'/telegram-notifications/BOT_TOKEN', WithDecryption:true})).then(r => console.log(r.Parameter.Value)).catch(() => process.exit(1));
")

TELEGRAM_CHAT_ID=$(node -e "
const {SSMClient, GetParameterCommand} = require('@aws-sdk/client-ssm');
const client = new SSMClient({region:'eu-central-1', credentials:{accessKeyId:process.env.AWS_ACCESS_KEY_ID, secretAccessKey:process.env.AWS_SECRET_ACCESS_KEY}});
client.send(new GetParameterCommand({Name:'/telegram-notifications/CHAT_ID'})).then(r => console.log(r.Parameter.Value)).catch(() => process.exit(1));
")

export TELEGRAM_BOT_TOKEN
export TELEGRAM_CHAT_ID

echo "✅ Переменные загружены"
echo ""

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
    npx serverless deploy --stage prod
else
    npx serverless deploy --stage dev
fi

echo ""
echo "✅ Деплой завершён!"
echo ""

