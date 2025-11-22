#!/bin/bash

# Скрипт для получения endpoint URL после деплоя

set -e

STAGE=${1:-dev}
REGION=${2:-eu-central-1}

echo "🔍 Получение endpoint для stage: $STAGE, region: $REGION"

# Способ 1: Через serverless info
if command -v serverless &> /dev/null; then
  ENDPOINT=$(npx serverless info --stage $STAGE 2>&1 | grep -oP 'https://[^\s]+' | head -1 || echo "")
  
  if [ -n "$ENDPOINT" ]; then
    echo "✅ Endpoint найден через serverless info:"
    echo "$ENDPOINT"
    exit 0
  fi
fi

# Способ 2: Через AWS CLI
if command -v aws &> /dev/null; then
  ENDPOINT=$(aws apigatewayv2 get-apis \
    --region $REGION \
    --query "Items[?contains(Name, 'telegram-notifications-service-$STAGE')].ApiEndpoint" \
    --output text 2>/dev/null | head -1 || echo "")
  
  if [ -n "$ENDPOINT" ]; then
    echo "✅ Endpoint найден через AWS CLI:"
    echo "$ENDPOINT"
    exit 0
  fi
fi

# Способ 3: Через CloudFormation
if command -v aws &> /dev/null; then
  STACK_NAME="telegram-notifications-service-$STAGE"
  
  ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query "Stacks[0].Outputs[?OutputKey=='ServiceEndpoint'].OutputValue" \
    --output text 2>/dev/null || echo "")
  
  if [ -n "$ENDPOINT" ]; then
    echo "✅ Endpoint найден через CloudFormation:"
    echo "$ENDPOINT"
    exit 0
  fi
fi

echo "❌ Endpoint не найден"
echo "💡 Попробуйте:"
echo "   1. Проверить что деплой завершён успешно"
echo "   2. Проверить AWS credentials"
echo "   3. Проверить что stack существует: aws cloudformation describe-stacks --stack-name telegram-notifications-service-$STAGE --region $REGION"
exit 1

