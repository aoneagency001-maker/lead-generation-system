#!/bin/bash

# Скрипт для проверки настроенных GitHub Secrets
# Требует: gh CLI установлен и авторизован

set -e

echo "🔍 Проверка GitHub Secrets для деплоя"
echo "======================================"
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

# Получаем список секретов
echo "🔍 Проверка секретов..."
SECRETS=$(gh secret list --repo "$REPO" 2>/dev/null | awk '{print $1}' || echo "")

# Список обязательных секретов для деплоя
REQUIRED_SECRETS=(
  "VPS_HOST"
  "VPS_USER"
  "VPS_SSH_KEY"
)

# Список опциональных секретов
OPTIONAL_SECRETS=(
  "VPS_DEPLOY_PATH"
  "TELEGRAM_BOT_TOKEN"
  "TELEGRAM_MONITOR_BOT_TOKEN"
  "OPENAI_API_KEY"
  "SUPABASE_URL"
  "SUPABASE_KEY"
)

echo "📋 Обязательные секреты для деплоя:"
echo ""

MISSING=0
for secret in "${REQUIRED_SECRETS[@]}"; do
  if echo "$SECRETS" | grep -q "^$secret$"; then
    echo "  ✅ $secret"
  else
    echo "  ❌ $secret - ОТСУТСТВУЕТ"
    MISSING=$((MISSING + 1))
  fi
done

echo ""
echo "📋 Опциональные секреты:"
echo ""

for secret in "${OPTIONAL_SECRETS[@]}"; do
  if echo "$SECRETS" | grep -q "^$secret$"; then
    echo "  ✅ $secret"
  else
    echo "  ⚠️  $secret - не настроен (опционально)"
  fi
done

echo ""

if [ $MISSING -gt 0 ]; then
  echo "❌ Найдено $MISSING отсутствующих обязательных секретов!"
  echo ""
  echo "📝 Как добавить:"
  echo "   1. Откройте: https://github.com/$REPO/settings/secrets/actions"
  echo "   2. Нажмите 'New repository secret'"
  echo "   3. Добавьте отсутствующие секреты"
  echo ""
  echo "💡 Или используйте скрипт:"
  echo "   ./scripts/setup_github_secrets.sh"
  exit 1
else
  echo "✅ Все обязательные секреты настроены!"
  echo ""
  echo "🔍 Проверка формата SSH ключа..."
  
  # Проверяем формат SSH ключа (если есть доступ)
  SSH_KEY=$(gh secret get VPS_SSH_KEY --repo "$REPO" 2>/dev/null || echo "")
  
  if [ -z "$SSH_KEY" ]; then
    echo "⚠️  Не удалось проверить формат SSH ключа (нужны права на чтение)"
  else
    if echo "$SSH_KEY" | grep -q "BEGIN.*PRIVATE KEY"; then
      echo "✅ SSH ключ имеет правильный формат (содержит BEGIN/END)"
    else
      echo "⚠️  SSH ключ может быть в неправильном формате"
      echo "   Убедитесь, что ключ содержит строки:"
      echo "   -----BEGIN OPENSSH PRIVATE KEY-----"
      echo "   ..."
      echo "   -----END OPENSSH PRIVATE KEY-----"
    fi
  fi
fi

echo ""
echo "✅ Проверка завершена"

