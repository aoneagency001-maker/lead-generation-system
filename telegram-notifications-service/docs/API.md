# 📡 API Documentation

**Версия:** 2.0.0  
**Base URL:** `https://{api-id}.execute-api.{region}.amazonaws.com/{stage}`

---

## Общие принципы

### Аутентификация

В текущей версии аутентификация не требуется. Для production рекомендуется добавить API ключи или JWT токены.

### Формат ответов

Все ответы в формате JSON:

**Успешный ответ:**
```json
{
  "success": true,
  "data": { ... },
  "requestId": "abc123"
}
```

**Ошибка:**
```json
{
  "success": false,
  "error": "Error message",
  "requestId": "abc123"
}
```

### Коды статусов

- `200` - Успешный запрос
- `400` - Неверный запрос (валидация)
- `500` - Внутренняя ошибка сервера

### Rate Limiting

По умолчанию API Gateway имеет лимит 10,000 запросов/секунду. Для production можно настроить кастомные лимиты.

---

## Endpoints

### POST `/track-visitor`

Отслеживает посетителя и отправляет уведомление в Telegram.

#### Request

**Headers:**
```
Content-Type: application/json
User-Agent: Mozilla/5.0... (опционально, извлекается автоматически)
```

**Body:**
```json
{
  "clientId": "client_001",           // Обязательно: ID клиента
  "page": "/",                         // Текущая страница
  "landingPage": "/",                  // Лендинг (первая страница)
  "referrer": "https://yandex.kz",    // Реферер
  "screenResolution": "1920x1080",    // Разрешение экрана
  "sessionId": "abc-123",             // ID сессии (генерируется автоматически если не указан)
  "utmSource": "yandex",              // UTM source
  "utmMedium": "cpc",                 // UTM medium
  "utmCampaign": "roofing",           // UTM campaign
  "utmTerm": "ремонт крыши",          // UTM term
  "utmContent": "banner_1",           // UTM content
  "isFirstVisit": true,               // Первый визит
  "timeOnSite": 120,                  // Время на сайте (секунды)
  "pagesViewed": 3,                   // Количество просмотренных страниц
  "clicks": 5,                        // Количество кликов
  "conversions": ["purchase", "signup"] // Массив конверсий
}
```

**Минимальный запрос:**
```json
{
  "clientId": "client_001",
  "page": "/"
}
```

#### Response

**Успех (200):**
```json
{
  "tracked": true,
  "visitorId": "550e8400-e29b-41d4-a716-446655440000",
  "requestId": "abc123"
}
```

**Бот обнаружен (200):**
```json
{
  "tracked": false,
  "message": "Bot detected, not tracked",
  "requestId": "abc123"
}
```

**Ошибка валидации (400):**
```json
{
  "tracked": false,
  "error": "Invalid payload",
  "requestId": "abc123"
}
```

#### Примеры

**cURL:**
```bash
curl -X POST https://api.example.com/track-visitor \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "client_001",
    "page": "/",
    "referrer": "https://google.com",
    "utmSource": "yandex",
    "utmMedium": "cpc"
  }'
```

**JavaScript:**
```javascript
fetch('https://api.example.com/track-visitor', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    clientId: 'client_001',
    page: window.location.pathname,
    referrer: document.referrer,
    screenResolution: `${screen.width}x${screen.height}`,
    sessionId: getSessionId(),
    utmSource: getUrlParam('utm_source'),
    utmMedium: getUrlParam('utm_medium'),
  }),
});
```

---

### POST `/tilda-webhook`

Обрабатывает webhook от Tilda и отправляет уведомление в Telegram.

#### Request

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "name": "Иван Иванов",                    // Имя
  "phone": "+7 777 123 45 67",              // Телефон (обязательно если нет email)
  "email": "ivan@example.com",              // Email (обязательно если нет phone)
  "message": "Хочу заказать разработку",    // Сообщение
  "formName": "Contact Form",               // Название формы
  "pageUrl": "https://example.com/contact", // URL страницы
  "clientId": "client_001",                 // ID клиента (опционально)
  "answers": {                              // Для квизов
    "question1": "answer1",
    "question2": "answer2"
  }
}
```

**Минимальный запрос:**
```json
{
  "phone": "+7 777 123 45 67"
}
```

#### Response

**Успех (200):**
```json
{
  "success": true,
  "message": "Notification sent",
  "requestId": "abc123"
}
```

**Ошибка валидации (400):**
```json
{
  "success": false,
  "message": "Invalid payload: phone or email is required",
  "requestId": "abc123"
}
```

#### Примеры

**Настройка в Tilda:**
1. Откройте настройки формы
2. Перейдите в "Отправка данных" → "Webhook"
3. URL: `https://api.example.com/tilda-webhook`
4. Метод: POST
5. Content-Type: application/json

**Тестовый запрос:**
```bash
curl -X POST https://api.example.com/tilda-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Тестовый пользователь",
    "phone": "+7 777 123 45 67",
    "email": "test@example.com",
    "message": "Тестовое сообщение"
  }'
```

---

### POST `/metrika-webhook`

Обрабатывает события из Яндекс.Метрики.

#### Request

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "clientId": "client_001",              // ID клиента
  "counterId": "12345678",               // ID счётчика Метрики
  "sessionId": "session-123",           // ID сессии
  "visitId": "visit-123",                // ID визита
  "eventName": "purchase",              // Название события
  "eventParams": {                      // Параметры события
    "order_id": "order-123",
    "revenue": 5000,
    "currency": "RUB"
  }
}
```

#### Response

**Успех (200):**
```json
{
  "success": true,
  "message": "Event processed",
  "requestId": "abc123"
}
```

#### Примеры

```bash
curl -X POST https://api.example.com/metrika-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "client_001",
    "counterId": "12345678",
    "eventName": "purchase",
    "eventParams": {
      "revenue": 5000
    }
  }'
```

---

### GET `/health`

Проверка работоспособности сервиса.

#### Request

Нет параметров.

#### Response

**Успех (200):**
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

**Проблемы:**
```json
{
  "status": "degraded",
  "service": "telegram-notifications-service",
  "version": "2.0.0",
  "timestamp": "2025-11-21T12:00:00.000Z",
  "environment": "dev",
  "checks": {
    "dynamodb": true,
    "telegram": false
  }
}
```

#### Примеры

```bash
curl https://api.example.com/health
```

---

## Типы данных

### VisitEvent

```typescript
{
  type: 'VISIT';
  id: string;
  clientId: string;
  sessionId?: string;
  ip: string;
  country: string;
  city: string;
  region?: string;
  timezone?: string;
  isp?: string;
  userAgent: string;
  device: 'mobile' | 'tablet' | 'desktop';
  browser?: string;
  os?: string;
  screenResolution?: string;
  referrer: string | null;
  page: string;
  landingPage: string;
  utmSource?: string | null;
  utmMedium?: string | null;
  utmCampaign?: string | null;
  utmTerm?: string | null;
  utmContent?: string | null;
  timeOnSite?: number;
  clicks?: number;
  pagesViewed?: number;
  conversions?: string[];
  timestamp: string; // ISO 8601
  source: 'tracker';
}
```

### FormEvent

```typescript
{
  type: 'FORM';
  id: string;
  clientId: string;
  formType: 'contact' | 'callback' | 'custom' | 'quiz';
  name?: string;
  email?: string;
  phone?: string;
  message?: string;
  answers?: Record<string, unknown>;
  ip: string;
  userAgent: string;
  pageUrl?: string;
  formName?: string;
  submittedAt: string; // ISO 8601
  timestamp: string; // ISO 8601
  source: 'tilda' | 'tracker' | 'manual';
}
```

### MetrikaEvent

```typescript
{
  type: 'METRIKA';
  id: string;
  clientId: string;
  counterId: string;
  visitId?: string;
  sessionId?: string;
  eventName?: string;
  eventParams?: Record<string, unknown>;
  enriched?: boolean;
  matchedVisitId?: string;
  timestamp: string; // ISO 8601
  source: 'metrika';
}
```

---

## Ошибки

### Коды ошибок

| Код | Описание |
|-----|----------|
| `400` | Неверный запрос (валидация) |
| `500` | Внутренняя ошибка сервера |

### Формат ошибки

```json
{
  "success": false,
  "error": "Error message",
  "requestId": "abc123"
}
```

### Типичные ошибки

**Неверный clientId:**
```json
{
  "tracked": false,
  "error": "Invalid payload",
  "requestId": "abc123"
}
```

**Отсутствует обязательное поле:**
```json
{
  "success": false,
  "message": "Invalid payload: phone or email is required",
  "requestId": "abc123"
}
```

---

## Best Practices

### 1. Всегда указывайте clientId

Это необходимо для правильной маршрутизации данных.

### 2. Используйте sessionId

Для отслеживания одного пользователя на разных страницах используйте один `sessionId`.

### 3. Отправляйте события асинхронно

Не блокируйте основной поток приложения:

```javascript
// Правильно
fetch('/track-visitor', { ... }).catch(() => {});

// Неправильно
await fetch('/track-visitor', { ... }); // блокирует UI
```

### 4. Обрабатывайте ошибки

Всегда обрабатывайте возможные ошибки:

```javascript
try {
  const response = await fetch('/track-visitor', { ... });
  const data = await response.json();
  if (!data.tracked) {
    console.warn('Tracking failed:', data.message);
  }
} catch (error) {
  console.error('Network error:', error);
}
```

### 5. Не отправляйте чувствительные данные

Не включайте пароли, токены, персональные данные в payload.

---

## Rate Limits

- **API Gateway:** 10,000 запросов/секунду (по умолчанию)
- **Lambda:** Автоматическое масштабирование
- **DynamoDB:** Pay-per-request, неограниченная пропускная способность
- **Telegram API:** 30 сообщений/секунду на бота
- **ip-api.com:** 45 запросов/минуту (бесплатный план)

---

## Версионирование

Текущая версия API: **2.0.0**

В будущем может быть добавлено версионирование через заголовок:
```
API-Version: 2.0
```

---

## Поддержка

При возникновении проблем:
1. Проверьте логи в CloudWatch
2. Проверьте формат запроса
3. Проверьте переменные окружения
4. Откройте issue в репозитории

