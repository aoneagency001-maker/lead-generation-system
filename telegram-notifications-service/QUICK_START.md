# 🚀 Quick Start Guide

**Для быстрого старта после деплоя**

---

## ✅ Что уже сделано

- ✅ Сервис развёрнут на AWS Lambda
- ✅ Endpoints доступны
- ✅ Telegram бот настроен
- ✅ DynamoDB таблица создана

---

## 🌐 Ваши endpoints

**Base URL:** `https://cppf0omfz6.execute-api.eu-central-1.amazonaws.com`

### Endpoints:

- **POST** `/track-visitor` - Отслеживание посетителей
- **POST** `/tilda-webhook` - Обработка заявок с Tilda
- **POST** `/metrika-webhook` - События из Яндекс.Метрики
- **GET** `/health` - Health check

---

## 🔗 Интеграция с Tilda

1. Откройте Tilda → Настройки формы → Отправка данных
2. Выберите "Webhook"
3. URL: `https://cppf0omfz6.execute-api.eu-central-1.amazonaws.com/tilda-webhook`
4. Метод: POST
5. Content-Type: application/json
6. Сохраните

---

## 📱 JavaScript трекинг на сайте

Добавьте на ваш сайт:

```html
<script>
(function() {
  // Отправка события визита
  fetch('https://cppf0omfz6.execute-api.eu-central-1.amazonaws.com/track-visitor', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      clientId: 'your_client_id', // Замените на ваш ID
      page: window.location.pathname,
      referrer: document.referrer,
      screenResolution: screen.width + 'x' + screen.height,
      sessionId: getSessionId(), // Ваша функция для получения sessionId
      utmSource: new URLSearchParams(window.location.search).get('utm_source'),
      utmMedium: new URLSearchParams(window.location.search).get('utm_medium'),
      utmCampaign: new URLSearchParams(window.location.search).get('utm_campaign'),
      utmTerm: new URLSearchParams(window.location.search).get('utm_term'),
      utmContent: new URLSearchParams(window.location.search).get('utm_content'),
    }),
  }).catch(() => {}); // Не блокируем основной поток
  
  // Функция для получения sessionId (пример)
  function getSessionId() {
    let sessionId = sessionStorage.getItem('sessionId');
    if (!sessionId) {
      sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      sessionStorage.setItem('sessionId', sessionId);
    }
    return sessionId;
  }
})();
</script>
```

---

## 🧪 Тестирование

### Health Check

```bash
curl https://cppf0omfz6.execute-api.eu-central-1.amazonaws.com/health
```

### Тест отслеживания

```bash
curl -X POST https://cppf0omfz6.execute-api.eu-central-1.amazonaws.com/track-visitor \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0" \
  -d '{
    "clientId": "test",
    "page": "/test",
    "referrer": "https://google.com",
    "utmSource": "yandex"
  }'
```

### Тест Tilda webhook

```bash
curl -X POST https://cppf0omfz6.execute-api.eu-central-1.amazonaws.com/tilda-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Тест",
    "phone": "+7 777 123 45 67",
    "email": "test@example.com",
    "message": "Тестовое сообщение"
  }'
```

---

## 📊 Мониторинг

### CloudWatch Logs

Просмотр логов:
1. Откройте [AWS CloudWatch Console](https://console.aws.amazon.com/cloudwatch/)
2. Перейдите в Logs → Log groups
3. Найдите: `/aws/lambda/telegram-notifications-service-dev-*`

### CloudWatch Metrics

Просмотр метрик:
1. CloudWatch → Metrics → Custom Namespaces
2. Найдите: `TelegramNotifications/dev`

---

## 🔄 Обновление

Для обновления кода:

```bash
cd telegram-notifications-service
npm run build
./scripts/deploy-with-env.sh dev
```

---

## 📚 Документация

- **DEPLOYMENT_SUCCESS.md** - результаты деплоя
- **DEPLOYED.md** - информация о сервисе
- **DEPLOYMENT.md** - инструкция по деплою
- **README.md** - общая документация
- **docs/ARCHITECTURE.md** - архитектура
- **docs/API.md** - API документация

---

**Готово к использованию!** 🎉

