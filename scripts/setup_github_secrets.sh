#!/bin/bash

# Скрипт для добавления секретов в GitHub через GitHub CLI
# Требует: gh CLI установлен и авторизован

set -e

echo "🔐 Настройка GitHub Secrets"
echo ""

# Проверяем наличие gh CLI
if ! command -v gh &> /dev/null; then
  echo "❌ GitHub CLI (gh) не установлен"
  echo ""
  echo "Установка:"
  echo "  brew install gh"
  echo "  gh auth login"
  exit 1
fi

# Проверяем авторизацию
if ! gh auth status &> /dev/null; then
  echo "❌ Не авторизован в GitHub CLI"
  echo ""
  echo "Авторизация:"
  echo "  gh auth login"
  exit 1
fi

# Получаем owner/repo из git remote
REPO_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$REPO_URL" ]; then
  echo "❌ Не удалось определить репозиторий"
  exit 1
fi

# Парсим owner/repo
if [[ $REPO_URL == *"github.com"* ]]; then
  REPO=$(echo $REPO_URL | sed -E 's/.*github.com[:/]([^/]+\/[^/]+)(\.git)?$/\1/')
else
  echo "❌ Не удалось определить owner/repo из URL: $REPO_URL"
  exit 1
fi

echo "📦 Репозиторий: $REPO"
echo ""

# Список секретов для добавления
SECRETS=(
  "TELEGRAM_BOT_TOKEN"
  "TELEGRAM_MONITOR_BOT_TOKEN"
  "TELEGRAM_ASSISTANT_BOT_TOKEN"
  "OPENAI_API_KEY"
  "ANTHROPIC_API_KEY"
  "PERPLEXITY_API_KEY"
  "SUPABASE_URL"
  "SUPABASE_KEY"
  "SUPABASE_SERVICE_KEY"
  "YANDEX_METRIKA_TOKEN"
  "GOOGLE_ANALYTICS_PROPERTY_ID"
  "VPS_HOST"
  "VPS_USER"
  "VPS_SSH_KEY"
)

echo "📋 Секреты для добавления:"
for secret in "${SECRETS[@]}"; do
  echo "  - $secret"
done
echo ""

# Проверяем существующие секреты
echo "🔍 Проверка существующих секретов..."
EXISTING=$(gh secret list --repo "$REPO" 2>/dev/null | awk '{print $1}' || echo "")

# Добавляем секреты
for secret in "${SECRETS[@]}"; do
  # Проверяем, существует ли секрет
  if echo "$EXISTING" | grep -q "^$secret$"; then
    echo "⚠️  $secret уже существует, пропускаем"
    continue
  fi
  
  # Запрашиваем значение
  echo ""
  read -sp "Введите значение для $secret: " value
  echo ""
  
  if [ -z "$value" ]; then
    echo "⚠️  Пустое значение, пропускаем $secret"
    continue
  fi
  
  # Добавляем секрет
  echo "$value" | gh secret set "$secret" --repo "$REPO"
  echo "✅ $secret добавлен"
done

echo ""
echo "✅ Настройка завершена!"
echo ""
echo "Проверка:"
echo "  gh secret list --repo $REPO"

