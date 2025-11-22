#!/bin/bash

# Скрипт для проверки GitHub Secrets через GitHub API
# Требует GITHUB_TOKEN в переменных окружения

set -e

echo "🔍 Проверка GitHub Secrets..."
echo ""

# Проверяем наличие GITHUB_TOKEN
if [ -z "$GITHUB_TOKEN" ]; then
  echo "⚠️  GITHUB_TOKEN не установлен"
  echo ""
  echo "💡 Для проверки secrets через API нужен GitHub Personal Access Token:"
  echo "   1. Создайте токен: https://github.com/settings/tokens"
  echo "   2. Права: repo (для private) или public_repo (для public)"
  echo "   3. Экспортируйте: export GITHUB_TOKEN=your_token"
  echo ""
  echo "📋 Или проверьте вручную:"
  echo "   https://github.com/{owner}/{repo}/settings/secrets/actions"
  echo ""
  exit 0
fi

# Получаем owner и repo из git remote
REPO_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$REPO_URL" ]; then
  echo "❌ Не удалось определить репозиторий"
  exit 1
fi

# Парсим owner/repo из URL
if [[ $REPO_URL == *"github.com"* ]]; then
  REPO=$(echo $REPO_URL | sed -E 's/.*github.com[:/]([^/]+\/[^/]+)(\.git)?$/\1/')
else
  echo "❌ Не удалось определить owner/repo из URL: $REPO_URL"
  exit 1
fi

echo "📦 Репозиторий: $REPO"
echo ""

# Проверяем secrets через GitHub API
REQUIRED_SECRETS=("AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY")

for SECRET in "${REQUIRED_SECRETS[@]}"; do
  echo -n "Проверка $SECRET... "
  
  # GitHub API не позволяет читать значения secrets, только проверить наличие
  # Поэтому мы проверяем что secret существует через список всех secrets
  SECRETS_LIST=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/$REPO/actions/secrets" 2>/dev/null || echo "")
  
  if echo "$SECRETS_LIST" | grep -q "\"name\":\"$SECRET\""; then
    echo "✅ Найден"
  else
    echo "❌ Не найден"
    echo "   Добавьте: https://github.com/$REPO/settings/secrets/actions"
  fi
done

echo ""
echo "✅ Проверка завершена"
echo ""
echo "💡 Если все secrets найдены, можно запустить тестовый деплой:"
echo "   1. Откройте: https://github.com/$REPO/actions"
echo "   2. Выберите '🚀 Deploy to AWS Lambda'"
echo "   3. Нажмите 'Run workflow'"
echo "   4. Выберите stage: dev"
echo "   5. Нажмите 'Run workflow'"

