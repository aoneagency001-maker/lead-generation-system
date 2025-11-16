# Модуль 4: Sales Handoff (Передача лидов)

Автоматическая передача квалифицированных лидов предпринимателю через различные каналы.

## Функции

- **Мгновенные уведомления**: Telegram, Email, SMS
- **n8n workflows**: Визуальная автоматизация без кода
- **CRM интеграция**: Supabase + NocoDB
- **Приоритизация**: Горячие лиды передаются первыми

## Установка

```bash
# Запустите n8n
docker-compose up -d n8n

# Откройте UI
open http://localhost:5678
```

## Настройка n8n Workflow

1. Откройте n8n UI
2. Создайте новый workflow
3. Добавьте триггер "Webhook"
4. Добавьте узлы уведомлений

Пример workflow:

```
[Webhook] → [Фильтр по качеству] → [Telegram] → [Email] → [Supabase]
```

## Использование

### Отправка уведомления

```python
from modules.sales_handoff.notifiers.apprise_client import send_notification

send_notification(
    title="Новый горячий лид!",
    message="Иван, +77001234567, готов купить сегодня",
    channels=["telegram", "email"]
)
```

### Интеграция с Модулем 3

```python
# После квалификации лида
if lead.quality_score > 80:
    # Отправить уведомление
    send_notification(
        title=f"Горячий лид: {lead.name}",
        message=f"Телефон: {lead.phone}\nБюджет: {lead.budget} тг",
        urgent=True
    )
```

## Конфигурация

```bash
# .env
TELEGRAM_NOTIFICATION_CHAT_ID=your-chat-id
ENABLE_NOTIFICATIONS=True
NOTIFICATION_CHANNELS=telegram,email
```

## n8n Workflows (примеры)

### 1. Простое уведомление

```json
{
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "new-lead"
      }
    },
    {
      "name": "Telegram",
      "type": "n8n-nodes-base.telegram",
      "parameters": {
        "text": "Новый лид: {{$json.name}}"
      }
    }
  ]
}
```

### 2. С фильтрацией

Только горячие лиды (quality_score > 80) отправляются предпринимателю.

## TODO

- [ ] SMS уведомления (через Казахтелеком API)
- [ ] Push уведомления в мобильное приложение
- [ ] Автоматический звонок через VoIP

