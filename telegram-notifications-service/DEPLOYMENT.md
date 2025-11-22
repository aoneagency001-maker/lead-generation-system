# 🚀 Инструкция по деплою на AWS

**Актуально на ноябрь 2025**  
**Best practices для production**

---

## 📋 Предварительные требования

1. **AWS Account** с настроенными credentials
2. **Node.js >= 18.0.0**
3. **Serverless Framework** установлен глобально
4. **Telegram Bot Token** и Chat ID
5. **Яндекс.Метрика Token** (опционально, для интеграции)

---

## 🔧 Шаг 1: Установка зависимостей

```bash
# Установка Serverless Framework глобально
npm install -g serverless

# Установка зависимостей проекта
cd telegram-notifications-service
npm install
```

---

## 🔐 Шаг 2: Настройка AWS Credentials

### Вариант A: AWS CLI (рекомендуется)

```bash
aws configure
```

Введите:
- AWS Access Key ID
- AWS Secret Access Key
- Default region: `eu-central-1` (или ваш регион)
- Default output format: `json`

### Вариант B: Переменные окружения

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=eu-central-1
```

---

## 🔑 Шаг 3: Сохранение секретов в AWS Systems Manager

### Telegram Bot Token

```bash
aws ssm put-parameter \
  --name "/telegram-notifications/BOT_TOKEN" \
  --value "your_bot_token_here" \
  --type "SecureString" \
  --region eu-central-1 \
  --overwrite
```

### Telegram Chat ID

```bash
aws ssm put-parameter \
  --name "/telegram-notifications/CHAT_ID" \
  --value "your_chat_id_here" \
  --type "String" \
  --region eu-central-1 \
  --overwrite
```

### Яндекс.Метрика Token (опционально)

```bash
aws ssm put-parameter \
  --name "/telegram-notifications/METRIKA_TOKEN" \
  --value "your_metrika_token_here" \
  --type "SecureString" \
  --region eu-central-1 \
  --overwrite
```

### Яндекс.Метрика Counter ID (опционально)

```bash
aws ssm put-parameter \
  --name "/telegram-notifications/METRIKA_COUNTER_ID" \
  --value "your_counter_id_here" \
  --type "String" \
  --region eu-central-1 \
  --overwrite
```

---

## 🏗 Шаг 4: Сборка проекта

```bash
npm run build
```

Проверьте, что папка `dist/` создана и содержит скомпилированные файлы.

---

## 🚀 Шаг 5: Деплой

### Деплой в dev окружение

```bash
npm run deploy:dev
```

или

```bash
serverless deploy --stage dev
```

### Деплой в production

```bash
npm run deploy:prod
```

или

```bash
serverless deploy --stage prod
```

### Что происходит при деплое:

1. ✅ Создаются Lambda функции (track-visitor, tilda-webhook, metrika-webhook, health)
2. ✅ Создаётся API Gateway с endpoints
3. ✅ Создаётся DynamoDB таблица для событий
4. ✅ Настраиваются IAM роли с необходимыми правами
5. ✅ Настраиваются переменные окружения из SSM

---

## 📡 Шаг 6: Получение URL endpoint'ов

После успешного деплоя выполните:

```bash
serverless info
```

Или:

```bash
serverless info --stage dev
```

Вы получите вывод вида:

```
Service Information
service: telegram-notifications-service
stage: dev
region: eu-central-1
stack: telegram-notifications-service-dev
resources: 15
api keys:
  None
endpoints:
  POST - https://{api-id}.execute-api.eu-central-1.amazonaws.com/track-visitor
  POST - https://{api-id}.execute-api.eu-central-1.amazonaws.com/tilda-webhook
  POST - https://{api-id}.execute-api.eu-central-1.amazonaws.com/metrika-webhook
  GET - https://{api-id}.execute-api.eu-central-1.amazonaws.com/health
functions:
  trackVisitor: telegram-notifications-service-dev-trackVisitor
  tildaWebhook: telegram-notifications-service-dev-tildaWebhook
  metrikaWebhook: telegram-notifications-service-dev-metrikaWebhook
  health: telegram-notifications-service-dev-health
```

**Сохраните эти URL** - они понадобятся для интеграции.

---

## 🧪 Шаг 7: Тестирование

### Health Check

```bash
curl https://{api-id}.execute-api.eu-central-1.amazonaws.com/{stage}/health
```

Ожидаемый ответ:

```json
{
  "status": "ok",
  "service": "telegram-notifications-service",
  "version": "2.0.0",
  "timestamp": "2025-11-21T12:00:00.000Z",
  "environment": "dev",
  "checks": {
    "dynamodb": true,
    "telegram": true
  }
}
```

### Тест track-visitor

```bash
curl -X POST https://{api-id}.execute-api.eu-central-1.amazonaws.com/{stage}/track-visitor \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "test_client",
    "page": "/test",
    "referrer": "https://google.com",
    "utmSource": "yandex",
    "utmMedium": "cpc"
  }'
```

### Тест tilda-webhook

```bash
curl -X POST https://{api-id}.execute-api.eu-central-1.amazonaws.com/{stage}/tilda-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Тестовый пользователь",
    "phone": "+7 777 123 45 67",
    "email": "test@example.com",
    "message": "Тестовое сообщение"
  }'
```

---

## 📊 Шаг 8: Мониторинг в CloudWatch

### Просмотр логов

1. Откройте [AWS CloudWatch Console](https://console.aws.amazon.com/cloudwatch/)
2. Перейдите в **Logs** → **Log groups**
3. Найдите группы:
   - `/aws/lambda/telegram-notifications-service-{stage}-trackVisitor`
   - `/aws/lambda/telegram-notifications-service-{stage}-tildaWebhook`
   - `/aws/lambda/telegram-notifications-service-{stage}-metrikaWebhook`

### Просмотр метрик

1. Перейдите в **Metrics** → **Custom Namespaces**
2. Найдите namespace: `TelegramNotifications/{stage}`
3. Доступные метрики:
   - `visit_events` - количество событий визитов
   - `form_events` - количество заявок
   - `metrika_events` - события из Метрики
   - `telegram_notifications` - отправленные уведомления
   - `errors` - ошибки по типам

### Настройка алертов

Рекомендуется настроить CloudWatch Alarms для:

1. **Высокий процент ошибок**
   - Метрика: `errors`
   - Условие: > 5% от общего количества запросов
   - Действие: отправка в SNS/Email

2. **Высокая длительность выполнения**
   - Метрика: `visit_duration`, `form_duration`
   - Условие: > 10 секунд
   - Действие: уведомление

3. **Проблемы с Telegram**
   - Метрика: `telegram_notifications` (Status=error)
   - Условие: > 0
   - Действие: немедленное уведомление

---

## 🔄 Шаг 9: Обновление (redeploy)

После изменений в коде:

```bash
# Сборка
npm run build

# Деплой
npm run deploy:dev  # или deploy:prod
```

Serverless Framework автоматически обновит только изменённые функции.

---

## 🗑 Шаг 10: Удаление (если нужно)

```bash
serverless remove --stage dev
```

⚠️ **Внимание:** Это удалит все ресурсы (Lambda, API Gateway, DynamoDB таблицу).

---

## 🔧 Настройка Tilda Webhook

1. Откройте настройки формы в Tilda
2. Перейдите в **Настройки формы** → **Отправка данных**
3. Выберите **Webhook**
4. URL: `https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/tilda-webhook`
5. Метод: **POST**
6. Content-Type: **application/json**
7. Сохраните настройки

---

## 📈 Интеграция с Яндекс.Метрикой

### Получение OAuth токена

1. Перейдите в [Яндекс OAuth](https://oauth.yandex.ru/)
2. Создайте приложение
3. Получите OAuth токен
4. Сохраните в SSM (см. Шаг 3)

### Использование Logs API

Сервис поддерживает два способа работы с Метрикой:

1. **Webhook** - Метрика отправляет события напрямую
   - Endpoint: `/metrika-webhook`
   - Настройка через Яндекс.Метрику

2. **Logs API** - периодический сбор данных
   - Используйте утилиту `metrika-client.ts`
   - Можно создать отдельную Lambda функцию по расписанию

### Пример Lambda функции для периодического сбора

```typescript
// src/handlers/metrika-sync.ts
import { getMetrikaLogs, downloadMetrikaLogPart } from '../utils/metrika-client';

export async function handler() {
  const token = process.env.METRIKA_TOKEN!;
  const counterId = process.env.METRIKA_COUNTER_ID!;
  
  // Получить логи за вчера
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const dateStr = yesterday.toISOString().split('T')[0];
  
  const logRequest = await getMetrikaLogs(token, {
    counterId,
    date1: dateStr,
    date2: dateStr,
  });
  
  if (logRequest) {
    // Обработать части логов
    // ...
  }
}
```

Добавьте в `serverless.yml`:

```yaml
metrikaSync:
  handler: dist/handlers/metrika-sync.handler
  description: Sync data from Yandex Metrika
  events:
    - schedule: rate(1 day)  # Каждый день
```

---

## 🐛 Troubleshooting

### Проблема: "Access Denied" при деплое

**Решение:** Проверьте AWS credentials и права доступа:
- Lambda
- API Gateway
- DynamoDB
- CloudWatch
- Systems Manager (SSM)

### Проблема: Lambda не может подключиться к DynamoDB

**Решение:** Проверьте IAM роли в `serverless.yml` - должны быть права на DynamoDB.

### Проблема: Telegram уведомления не отправляются

**Решение:**
1. Проверьте `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID` в SSM
2. Проверьте логи в CloudWatch
3. Убедитесь, что бот активен

### Проблема: Высокая задержка ответа

**Решение:**
1. Увеличьте `memorySize` в `serverless.yml` (больше памяти = быстрее CPU)
2. Проверьте таймауты внешних API (geo-location, telegram)

---

## 📚 Полезные ссылки

- [Serverless Framework Docs](https://www.serverless.com/framework/docs)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/WhatIsCloudWatchLogs.html)
- [Яндекс.Метрика Logs API](https://yandex.ru/dev/metrika/doc/api2/logs/about.html)

---

## ✅ Чеклист перед production деплоем

- [ ] AWS credentials настроены
- [ ] Секреты сохранены в SSM
- [ ] `npm install` выполнен
- [ ] `npm run build` успешно
- [ ] Локальное тестирование пройдено (`npm run offline`)
- [ ] Health check работает
- [ ] Тестовые запросы успешны
- [ ] CloudWatch логи проверены
- [ ] CloudWatch метрики настроены
- [ ] Алерты настроены
- [ ] Tilda webhook настроен
- [ ] Документация прочитана

---

**Готово!** 🎉 Микросервис развёрнут и готов к использованию.

