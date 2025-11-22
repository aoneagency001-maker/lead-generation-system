# 🔐 Информация о переменных окружения

**Дата создания:** 21.11.2025 05:19

---

## ✅ Настроенные параметры

### AWS Systems Manager Parameter Store

Все секреты хранятся в AWS SSM Parameter Store:

- ✅ `/telegram-notifications/BOT_TOKEN` - SecureString
- ✅ `/telegram-notifications/CHAT_ID` - String (280192618)

### Переменные окружения в Lambda

При деплое переменные загружаются из SSM и устанавливаются в Lambda:

- `TELEGRAM_BOT_TOKEN` - токен бота
- `TELEGRAM_CHAT_ID` - ID чата (280192618)
- `DYNAMODB_TABLE` - название таблицы (автоматически)
- `CLOUDWATCH_NAMESPACE` - namespace для метрик (автоматически)
- `NODE_ENV` - окружение (dev/prod)
- `LOG_LEVEL` - уровень логирования

---

## 📝 Для локальной разработки

Создайте файл `.env.local` (не коммитится в git):

```bash
# AWS
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=eu-central-1

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# DynamoDB
DYNAMODB_TABLE=telegram-notifications-events-dev

# CloudWatch
CLOUDWATCH_NAMESPACE=TelegramNotifications/dev

# Environment
NODE_ENV=development
LOG_LEVEL=debug
```

---

## 🔄 Обновление переменных

### Обновить Chat ID

```bash
node scripts/setup-aws.js <new_chat_id>
```

### Обновить Bot Token

```bash
aws ssm put-parameter \
  --name "/telegram-notifications/BOT_TOKEN" \
  --value "new_token" \
  --type "SecureString" \
  --region eu-central-1 \
  --overwrite
```

### Добавить параметры Метрики

```bash
aws ssm put-parameter \
  --name "/telegram-notifications/METRIKA_TOKEN" \
  --value "your_token" \
  --type "SecureString" \
  --region eu-central-1

aws ssm put-parameter \
  --name "/telegram-notifications/METRIKA_COUNTER_ID" \
  --value "your_counter_id" \
  --type "String" \
  --region eu-central-1
```

После обновления параметров в SSM нужно передеплоить:

```bash
./scripts/deploy-with-env.sh dev
```

---

## 🔒 Безопасность

⚠️ **Важно:**
- Никогда не коммитьте `.env` файлы в git
- Секреты хранятся только в AWS SSM
- При деплое переменные загружаются из SSM автоматически
- В коде нет хардкода секретов

---

## 📚 Дополнительная информация

- **DEPLOYED.md** - информация о развёрнутом сервисе
- **DEPLOYMENT.md** - инструкция по деплою
- **README.md** - общая документация

