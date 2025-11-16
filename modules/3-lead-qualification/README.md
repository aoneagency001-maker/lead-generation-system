# Модуль 3: Lead Qualification (Квалификация лидов)

Умные боты для WhatsApp и Telegram, которые автоматически общаются с клиентами и квалифицируют лиды.

## Функции

- **WhatsApp бот**: Через WAHA (self-hosted WhatsApp API)
- **Telegram бот**: Официальный Bot API
- **Умные сценарии**: Botpress для сложных диалогов
- **Квалификация**: Оценка бюджета, срочности, потребностей
- **История**: Сохранение всех диалогов в Supabase

## Установка

```bash
# Python зависимости
pip install python-telegram-bot telethon

# WhatsApp через Docker
docker-compose up -d waha
```

## Использование

### Telegram бот

```bash
# Создайте бота через @BotFather
# Добавьте токен в .env
python modules/3-lead-qualification/telegram_bot.py
```

### WhatsApp бот

```bash
# 1. Запустите WAHA
docker-compose up -d waha

# 2. Отсканируйте QR код
open http://localhost:3001

# 3. Запустите бота
python modules/3-lead-qualification/whatsapp_bot.py
```

## Пример диалога

```
Клиент: Здравствуйте, сколько стоит ремонт?
Бот: Добрый день! Какая модель телефона?
Клиент: iPhone 12
Бот: Что именно нужно отремонтировать?
Клиент: Экран разбился
Бот: Замена экрана iPhone 12 - 25000 тг. 
     Когда вам удобно приехать?
Клиент: Сегодня можно?
Бот: Отлично! Записываю вас на сегодня.
     Ваше имя и телефон?
```

После диалога лид автоматически сохраняется в базу с оценкой качества.

## Конфигурация сценариев

Файл `scenarios/qualification_flow.json`:

```json
{
  "name": "phone_repair_qualification",
  "steps": [
    {
      "id": "greeting",
      "message": "Здравствуйте! Чем могу помочь?",
      "next": "identify_need"
    },
    {
      "id": "identify_need",
      "type": "question",
      "message": "Какая модель телефона?",
      "extract": "phone_model",
      "next": "ask_issue"
    }
  ]
}
```

## TODO

- [ ] Интеграция с Botpress для сложных сценариев
- [ ] GPT-4 для более естественных ответов
- [ ] Голосовые сообщения (транскрипция)
- [ ] Мультиязычность (рус/каз/англ)

