#!/bin/bash

# Скрипт для добавления публичного SSH ключа на AWS EC2 через SSM
# Требует: AWS CLI настроен с правами на SSM

set -e

INSTANCE_ID="i-0fd42f4b1d227227e"
REGION="us-east-1"
PUBLIC_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMwT/Dn9wnIj/zQFK2rkK0vpCBIu0Ke/yxkmXZFNSeDS github-actions-deploy"

echo "🔐 Добавление SSH ключа на EC2 через AWS Systems Manager"
echo "========================================================="
echo ""
echo "Instance ID: $INSTANCE_ID"
echo "Region: $REGION"
echo ""

# Проверяем AWS CLI
if ! command -v aws &> /dev/null; then
  echo "❌ AWS CLI не установлен"
  echo "Установка: brew install awscli"
  exit 1
fi

# Проверяем авторизацию
if ! aws sts get-caller-identity &> /dev/null; then
  echo "❌ AWS CLI не авторизован"
  echo "Настройка: aws configure"
  exit 1
fi

echo "✅ AWS CLI настроен"
echo ""

# Команды для выполнения на сервере
COMMANDS=(
  "mkdir -p ~/.ssh"
  "chmod 700 ~/.ssh"
  "echo '$PUBLIC_KEY' >> ~/.ssh/authorized_keys"
  "chmod 600 ~/.ssh/authorized_keys"
  "cat ~/.ssh/authorized_keys | tail -1"
)

echo "📤 Отправка команды на сервер..."
echo ""

# Отправляем команду через SSM
COMMAND_ID=$(aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters "commands=$(printf '%s; ' "${COMMANDS[@]}")" \
  --region "$REGION" \
  --output text \
  --query 'Command.CommandId' 2>&1)

if [ $? -ne 0 ]; then
  echo "❌ Ошибка отправки команды:"
  echo "$COMMAND_ID"
  exit 1
fi

echo "✅ Команда отправлена. Command ID: $COMMAND_ID"
echo ""
echo "⏳ Ожидание выполнения (10 секунд)..."
sleep 10

# Проверяем результат
echo ""
echo "📋 Результат выполнения:"
echo ""

aws ssm get-command-invocation \
  --command-id "$COMMAND_ID" \
  --instance-id "$INSTANCE_ID" \
  --region "$REGION" \
  --query '[Status, StandardOutputContent, StandardErrorContent]' \
  --output text

echo ""
echo "✅ Проверка подключения..."
echo ""

# Проверяем подключение
if ssh -i ~/.ssh/github_actions_deploy -o ConnectTimeout=5 -o StrictHostKeyChecking=no ec2-user@13.220.11.94 "echo 'SSH connection successful'" 2>&1; then
  echo "✅ SSH подключение работает!"
else
  echo "⚠️ SSH подключение не работает. Проверь:"
  echo "   1. Публичный ключ добавлен на сервер"
  echo "   2. Security Group разрешает SSH (порт 22)"
  echo "   3. Правильный пользователь (ec2-user для Amazon Linux)"
fi

