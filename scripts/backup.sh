#!/bin/bash

# Скрипт для создания резервной копии проекта на локальной машине
# Запускается автоматически перед каждым деплоем

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$HOME/leadgen-backups"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
BACKUP_NAME="leadgen-backup-$TIMESTAMP"

echo "💾 Создание резервной копии проекта..."
echo "📁 Проект: $PROJECT_ROOT"
echo "📦 Имя бэкапа: $BACKUP_NAME"

# Создание директории для бэкапов
mkdir -p "$BACKUP_DIR"

# Создание резервной копии
cd "$PROJECT_ROOT"

tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  --exclude='*.log' \
  --exclude='.pytest_cache' \
  --exclude='.scrapy' \
  --exclude='playwright/.auth' \
  --exclude='node_modules' \
  --exclude='.DS_Store' \
  --exclude='uvicorn.pid' \
  .

# Сохранение .env отдельно (если существует)
if [ -f "$PROJECT_ROOT/.env" ]; then
  cp "$PROJECT_ROOT/.env" "$BACKUP_DIR/$BACKUP_NAME.env"
  echo "🔐 .env файл сохранен отдельно"
fi

# Удаление старых бэкапов (оставляем последние 20)
echo "🧹 Очистка старых бэкапов..."
cd "$BACKUP_DIR"
ls -t *.tar.gz 2>/dev/null | tail -n +21 | xargs rm -f || true
ls -t *.env 2>/dev/null | tail -n +21 | xargs rm -f || true

# Вывод статистики
BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME.tar.gz" | cut -f1)
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/*.tar.gz 2>/dev/null | wc -l | tr -d ' ')

echo ""
echo "✅ Резервная копия создана!"
echo "📦 Размер: $BACKUP_SIZE"
echo "📊 Всего бэкапов: $BACKUP_COUNT"
echo "📁 Путь: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
echo ""

# Создание симлинка на последний бэкап
ln -sf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" "$BACKUP_DIR/latest.tar.gz"
ln -sf "$BACKUP_DIR/$BACKUP_NAME.env" "$BACKUP_DIR/latest.env" 2>/dev/null || true

echo "🔗 Создан симлинк: $BACKUP_DIR/latest.tar.gz"

