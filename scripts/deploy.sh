#!/bin/bash

# Скрипт для ручного деплоя на VPS
# Использование: ./scripts/deploy.sh [production|staging]

set -e

ENVIRONMENT="${1:-production}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Загрузка конфигурации из .env
if [ -f "$PROJECT_ROOT/.env" ]; then
  export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

VPS_HOST="${VPS_HOST:-}"
VPS_USER="${VPS_USER:-root}"
VPS_DEPLOY_PATH="${VPS_DEPLOY_PATH:-/opt/lead-generation-system}"
BACKUP_PATH="/opt/backups/leadgen"

if [ -z "$VPS_HOST" ]; then
  echo "❌ Ошибка: VPS_HOST не установлен в .env"
  exit 1
fi

echo "🚀 Деплой на VPS"
echo "=================="
echo "🌐 Хост: $VPS_HOST"
echo "👤 Пользователь: $VPS_USER"
echo "📁 Путь: $VPS_DEPLOY_PATH"
echo "🔧 Окружение: $ENVIRONMENT"
echo ""

# Создание резервной копии перед деплоем
echo "💾 Создание локальной резервной копии..."
"$SCRIPT_DIR/backup.sh"

# Создание версии
VERSION=$(date +"%Y%m%d-%H%M%S")
echo "🏷️  Версия: $VERSION"

# Создание пакета для деплоя
echo "📦 Создание пакета для деплоя..."
cd "$PROJECT_ROOT"
mkdir -p deploy
tar -czf "deploy/leadgen-$VERSION.tar.gz" \
  --exclude='.git' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.env' \
  --exclude='*.log' \
  --exclude='.pytest_cache' \
  --exclude='.scrapy' \
  --exclude='playwright/.auth' \
  .

# Загрузка на VPS
echo "📤 Загрузка на VPS..."
scp -o StrictHostKeyChecking=no \
    "deploy/leadgen-$VERSION.tar.gz" \
    "$VPS_USER@$VPS_HOST:/tmp/"

# Деплой на VPS
echo "🚀 Развертывание на VPS..."
ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_HOST" << ENDSSH
  set -e
  
  echo "📦 Распаковка версии $VERSION..."
  mkdir -p "$VPS_DEPLOY_PATH"
  cd "$VPS_DEPLOY_PATH"
  
  # Создание резервной копии на VPS
  if [ -d "$VPS_DEPLOY_PATH" ] && [ "\$(ls -A $VPS_DEPLOY_PATH)" ]; then
    echo "💾 Создание резервной копии на VPS..."
    mkdir -p "$BACKUP_PATH"
    tar -czf "$BACKUP_PATH/backup-\$(date +%Y%m%d-%H%M%S).tar.gz" \
      --exclude='venv' \
      --exclude='__pycache__' \
      -C "$VPS_DEPLOY_PATH" .
    
    # Удаление старых бэкапов (оставляем последние 10)
    ls -t "$BACKUP_PATH"/*.tar.gz 2>/dev/null | tail -n +11 | xargs rm -f || true
  fi
  
  # Распаковка новой версии
  tar -xzf /tmp/leadgen-$VERSION.tar.gz -C "$VPS_DEPLOY_PATH"
  rm /tmp/leadgen-$VERSION.tar.gz
  
  # Копирование .env если существует
  if [ -f "$VPS_DEPLOY_PATH/.env.backup" ]; then
    cp "$VPS_DEPLOY_PATH/.env.backup" "$VPS_DEPLOY_PATH/.env"
  fi
  
  echo "✅ Версия $VERSION развернута"
ENDSSH

# Перезапуск сервисов
echo "🔄 Перезапуск сервисов..."
ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_HOST" << ENDSSH
  set -e
  
  cd "$VPS_DEPLOY_PATH"
  
  # Перезапуск Docker контейнеров
  if [ -f docker-compose.yml ]; then
    docker-compose down
    docker-compose up -d --build
  fi
  
  # Перезапуск systemd сервиса (если настроен)
  if systemctl is-active --quiet leadgen-api 2>/dev/null; then
    systemctl restart leadgen-api
  fi
  
  echo "✅ Сервисы перезапущены"
ENDSSH

# Health check
echo "✅ Проверка работоспособности..."
sleep 5
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  "http://$VPS_HOST/api/health" || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Health check passed (HTTP $HTTP_CODE)"
else
  echo "⚠️  Health check failed (HTTP $HTTP_CODE)"
  echo "Проверьте логи на VPS: ssh $VPS_USER@$VPS_HOST 'cd $VPS_DEPLOY_PATH && docker-compose logs'"
fi

# Очистка локального пакета
rm -f "deploy/leadgen-$VERSION.tar.gz"

echo ""
echo "✅ Деплой завершен!"
echo "🌐 Версия $VERSION развернута на $VPS_HOST"
echo "📁 Путь: $VPS_DEPLOY_PATH"

