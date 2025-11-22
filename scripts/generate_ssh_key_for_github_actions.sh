#!/bin/bash

# Скрипт для генерации SSH ключа для GitHub Actions
# Создаёт ключ, копирует публичный на VPS и показывает инструкции

set -e

echo "🔐 Генерация SSH ключа для GitHub Actions"
echo "=========================================="
echo ""

# Имя ключа
KEY_NAME="github_actions_deploy"
KEY_PATH="$HOME/.ssh/$KEY_NAME"

# Проверяем, существует ли ключ
if [ -f "$KEY_PATH" ]; then
  echo "⚠️  Ключ $KEY_PATH уже существует"
  read -p "Перезаписать? (yes/no): " overwrite
  if [ "$overwrite" != "yes" ]; then
    echo "❌ Отменено"
    exit 0
  fi
  rm -f "$KEY_PATH" "$KEY_PATH.pub"
fi

# Генерируем ключ
echo "🔑 Генерация SSH ключа..."
ssh-keygen -t ed25519 -C "github-actions-deploy" -f "$KEY_PATH" -N ""

echo ""
echo "✅ SSH ключ создан: $KEY_PATH"
echo ""

# Показываем публичный ключ
echo "📋 Публичный ключ (для добавления на VPS):"
echo "----------------------------------------"
cat "$KEY_PATH.pub"
echo "----------------------------------------"
echo ""

# Запрашиваем данные VPS
read -p "Введите IP или домен VPS: " VPS_HOST
read -p "Введите SSH пользователя (обычно 'root' или 'ubuntu'): " VPS_USER

if [ -z "$VPS_HOST" ] || [ -z "$VPS_USER" ]; then
  echo "⚠️  Данные VPS не введены, пропускаем копирование ключа"
else
  echo ""
  echo "📤 Копирование публичного ключа на VPS..."
  echo "   Команда: ssh-copy-id -i $KEY_PATH.pub $VPS_USER@$VPS_HOST"
  echo ""
  read -p "Выполнить копирование сейчас? (yes/no): " copy_now
  
  if [ "$copy_now" = "yes" ]; then
    ssh-copy-id -i "$KEY_PATH.pub" "$VPS_USER@$VPS_HOST" || {
      echo "⚠️  Автоматическое копирование не удалось"
      echo "   Выполните вручную:"
      echo "   ssh-copy-id -i $KEY_PATH.pub $VPS_USER@$VPS_HOST"
    }
  fi
fi

echo ""
echo "📋 Следующие шаги:"
echo ""
echo "1️⃣ Добавьте приватный ключ в GitHub Secrets:"
echo "   https://github.com/aoneagency001-maker/lead-generation-system/settings/secrets/actions"
echo ""
echo "   Secret name: VPS_SSH_KEY"
echo "   Secret value: (скопируйте ниже)"
echo ""
echo "----------------------------------------"
cat "$KEY_PATH"
echo "----------------------------------------"
echo ""
echo "2️⃣ Добавьте другие секреты:"
echo "   - VPS_HOST: $VPS_HOST"
echo "   - VPS_USER: $VPS_USER"
echo ""
echo "3️⃣ Проверьте настройку:"
echo "   ./scripts/check_github_secrets.sh"
echo ""
echo "4️⃣ Протестируйте подключение:"
echo "   ssh -i $KEY_PATH $VPS_USER@$VPS_HOST"
echo ""

