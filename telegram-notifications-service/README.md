# 📱 Telegram Notifications Service

**Production-ready микросервис трекинга и Telegram-уведомлений на AWS Lambda**

Версия: 2.0.0  
Статус: Production Ready ⚡

---

## 🎯 Что это?

Микросервис для отслеживания посетителей сайта и обработки заявок с лендингов с автоматической отправкой уведомлений в Telegram.

### Основные возможности

- ✅ **Отслеживание посетителей** (`/track-visitor`) - собирает данные о посетителях и отправляет уведомления
- ✅ **Tilda Webhook** (`/tilda-webhook`) - обработка заявок с лендингов Tilda
- ✅ **Яндекс.Метрика** (`/metrika-webhook`) - интеграция с Яндекс.Метрикой
- ✅ **Фильтрация ботов** - автоматическое исключение поисковых роботов
- ✅ **Геолокация по IP** - определение города и страны посетителя
- ✅ **Определение устройства** - мобильное/планшет/десктоп
- ✅ **UTM-метки** - отслеживание источников трафика
- ✅ **DynamoDB** - масштабируемое хранилище событий
- ✅ **CloudWatch** - логирование, метрики и мониторинг
- ✅ **Яндекс.Метрика Logs API** - интеграция для получения данных в реальном времени
- ✅ **CloudWatch Metrics** - автоматическая отправка метрик производительности

---

## 🏗 Архитектура

```
Сайт клиента (JS скрипт)
       │
       ▼
AWS API Gateway
       │
       ▼
Lambda Handler (track-visitor / tilda-webhook / metrika-webhook)
       │
       ├──► DynamoDB (сохранение событий)
       │
       └──► Telegram API (уведомления)
       │
       └──► CloudWatch Logs (логирование)
```

### Компоненты

- **API Gateway** - HTTP входная точка
- **Lambda Functions** - обработчики запросов
- **DynamoDB** - хранилище событий (pk = clientId, sk = type#timestamp#id)
- **Telegram Bot API** - отправка уведомлений
- **CloudWatch** - логи и мониторинг

---

## 📋 Требования

- Node.js >= 18.0.0
- npm или yarn
- AWS Account
- AWS CLI настроен
- Serverless Framework установлен глобально
- Telegram Bot Token и Chat ID

---

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
npm install
npm install -g serverless
```

### 2. Настройка AWS

```bash
# Настройка AWS credentials
aws configure

# Или через переменные окружения
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
```

### 3. Настройка переменных окружения

#### Вариант A: AWS Systems Manager Parameter Store (рекомендуется)

```bash
# Сохранить секреты в SSM
aws ssm put-parameter \
  --name "/telegram-notifications/BOT_TOKEN" \
  --value "your_bot_token" \
  --type "SecureString" \
  --region eu-central-1

aws ssm put-parameter \
  --name "/telegram-notifications/CHAT_ID" \
  --value "your_chat_id" \
  --type "String" \
  --region eu-central-1
```

#### Вариант B: Локальный .env файл (для разработки)

Создайте `.env` файл:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
DYNAMODB_TABLE=telegram-notifications-events-dev
AWS_REGION=eu-central-1
LOG_LEVEL=info
```

### 4. Сборка проекта

```bash
npm run build
```

### 5. Деплой

```bash
# Деплой в dev окружение
npm run deploy:dev

# Деплой в production
npm run deploy:prod
```

После деплоя вы получите URL endpoint'ов:

```
https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/
```

---

## 📡 API Endpoints

### POST `/track-visitor`

Отслеживает посетителя и отправляет уведомление в Telegram.

**Request:**

```json
{
  "clientId": "client_001",
  "page": "/",
  "landingPage": "/",
  "referrer": "https://yandex.kz",
  "screenResolution": "1920x1080",
  "sessionId": "abc-123",
  "utmSource": "yandex",
  "utmMedium": "cpc",
  "utmCampaign": "roofing",
  "utmTerm": "ремонт крыши",
  "utmContent": "banner_1",
  "isFirstVisit": true,
  "timeOnSite": 120,
  "pagesViewed": 3,
  "clicks": 5
}
```

**Response:**

```json
{
  "tracked": true,
  "visitorId": "uuid-visitor-id",
  "requestId": "abc123"
}
```

### POST `/tilda-webhook`

Обрабатывает webhook от Tilda и отправляет уведомление в Telegram.

**Request:**

```json
{
  "name": "Иван Иванов",
  "phone": "+7 777 123 45 67",
  "email": "ivan@example.com",
  "message": "Хочу заказать разработку сайта",
  "formName": "Contact Form",
  "pageUrl": "https://example.com/contact"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Notification sent",
  "requestId": "abc123"
}
```

### POST `/metrika-webhook`

Обрабатывает события из Яндекс.Метрики.

**Request:**

```json
{
  "clientId": "client_001",
  "counterId": "12345678",
  "sessionId": "session-123",
  "eventName": "purchase",
  "eventParams": {
    "order_id": "order-123",
    "revenue": 5000
  }
}
```

### GET `/health`

Проверка работоспособности сервиса.

**Response:**

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

---

## 🧪 Тестирование

### Локальное тестирование (offline)

```bash
# Запуск локально
npm run offline

# Тест отслеживания
curl -X POST http://localhost:3000/track-visitor \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "test_client",
    "page": "/test",
    "referrer": "https://google.com"
  }'
```

### Тестирование на AWS

```bash
# Получить URL после деплоя
serverless info

# Тест health endpoint
curl https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/health

# Тест track-visitor
curl -X POST https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/track-visitor \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "test_client",
    "page": "/test"
  }'
```

---

## 📊 База данных (DynamoDB)

### Структура таблицы

- **pk** (partition key) = `clientId`
- **sk** (sort key) = `type#timestamp#id`
- **payload** = полное событие в JSON
- **ttl** = автоматическая очистка через 90 дней

### Запросы

```typescript
// Получить все события клиента
getEvents('client_001')

// Получить только визиты
getEvents('client_001', 'VISIT')

// Найти визит по sessionId
findVisitBySessionId('client_001', 'session-123')
```

---

## 🔍 Мониторинг и логи

### CloudWatch Logs

Все логи автоматически попадают в CloudWatch:

- `/aws/lambda/telegram-notifications-service-dev-trackVisitor`
- `/aws/lambda/telegram-notifications-service-dev-tildaWebhook`
- `/aws/lambda/telegram-notifications-service-dev-metrikaWebhook`

### Префиксы логов

- `[TRACK-VISITOR]` - отслеживание посетителей
- `[TILDA-WEBHOOK]` - обработка Tilda webhook
- `[METRIKA-WEBHOOK]` - обработка Метрики
- `[TELEGRAM]` - отправка в Telegram
- `[STORAGE]` - работа с DynamoDB
- `[GEO-LOCATION]` - геолокация

### Алерты

Рекомендуется настроить CloudWatch Alarms для:
- Ошибок Lambda функций
- Высокой частоты ошибок
- Превышения лимитов DynamoDB

---

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | Обязательно |
|-----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | Да |
| `TELEGRAM_CHAT_ID` | ID чата для уведомлений | Да |
| `DYNAMODB_TABLE` | Название таблицы DynamoDB | Да |
| `METRIKA_TOKEN` | Токен Яндекс.Метрики | Нет |
| `METRIKA_COUNTER_ID` | ID счётчика Метрики | Нет |
| `NOTIFY_ON_METRIKA` | Отправлять уведомления о событиях Метрики | Нет |
| `LOG_LEVEL` | Уровень логирования (debug/info/warn/error) | Нет |

### Настройка serverless.yml

Основные параметры в `serverless.yml`:

- `provider.region` - регион AWS (по умолчанию: eu-central-1)
- `provider.memorySize` - память Lambda (по умолчанию: 256 MB)
- `provider.timeout` - таймаут Lambda (по умолчанию: 30 сек)

---

## 📝 Интеграция с Tilda

1. Откройте настройки формы в Tilda
2. Перейдите в "Настройки формы" → "Отправка данных"
3. Выберите "Webhook"
4. Укажите URL: `https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/tilda-webhook`
5. Сохраните настройки

---

## 🛠 Разработка

### Структура проекта

```
telegram-notifications-service/
├── src/
│   ├── handlers/          # Lambda handlers
│   │   ├── track-visitor.ts
│   │   ├── tilda-webhook.ts
│   │   ├── metrika-webhook.ts
│   │   └── health.ts
│   ├── utils/             # Утилиты
│   │   ├── logger.ts
│   │   ├── validators.ts
│   │   ├── geo-location.ts
│   │   ├── storage.ts
│   │   ├── telegram.ts
│   │   └── formatters.ts
│   └── types/             # TypeScript типы
│       ├── events.ts
│       └── index.ts
├── docs/                   # Документация
├── serverless.yml          # Serverless конфигурация
├── package.json
└── tsconfig.json
```

### Команды

```bash
# Сборка
npm run build

# Линтинг
npm run lint

# Форматирование
npm run format

# Деплой
npm run deploy

# Локальный запуск
npm run offline
```

---

## 📚 Дополнительная документация

- [ARCHITECTURE.md](./docs/ARCHITECTURE.md) - детальная архитектура
- [API.md](./docs/API.md) - полное описание API
- [DEPLOYMENT.md](./DEPLOYMENT.md) - пошаговая инструкция по деплою на AWS

---

## 🐛 Troubleshooting

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

## 📄 Лицензия

MIT

---

## 🤝 Поддержка

При возникновении проблем:
1. Проверьте логи в CloudWatch
2. Проверьте переменные окружения
3. Проверьте IAM права
4. Откройте issue в репозитории

