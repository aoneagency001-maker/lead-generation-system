# 🤖 Telegram Bot - Автосохранение подписчиков

## ⚡ Быстрый старт

### 1. Примени схему базы данных

**Через Supabase Dashboard:**
1. Открой Supabase → SQL Editor
2. Скопируй содержимое: `core/database/schema_telegram_bots.sql`
3. Вставь и выполни

**Или через psql:**
```bash
psql $DATABASE_URL -f core/database/schema_telegram_bots.sql
```

### 2. Запусти бота

```bash
python -m shared.telegram_bot
```

### 3. Отправь `/start` боту в Telegram

### 4. Проверь базу данных

```sql
SELECT * FROM telegram_bot_subscribers 
WHERE bot_type = 'monitor';
```

**Должен появиться твой chat_id! ✅**

---

## 📊 Что сохраняется

При нажатии `/start` автоматически сохраняется:

- ✅ `chat_id` - Telegram Chat ID
- ✅ `bot_type` - Тип бота (monitor, leads, sales)
- ✅ `username` - @username (если есть)
- ✅ `first_name` - Имя пользователя
- ✅ `last_name` - Фамилия
- ✅ `language_code` - Язык (ru, en, kk)
- ✅ `subscribed_at` - Дата подписки
- ✅ `last_activity_at` - Последняя активность

---

## 🔍 Полезные запросы

### Все подписчики monitor бота:
```sql
SELECT chat_id, username, first_name, status, subscribed_at
FROM telegram_bot_subscribers
WHERE bot_type = 'monitor'
ORDER BY subscribed_at DESC;
```

### Статистика по ботам:
```sql
SELECT bot_type, COUNT(*) as subscribers
FROM telegram_bot_subscribers
GROUP BY bot_type;
```

---

## 📚 Полная документация

**Детальный гайд:** `MD/v0.3/19.11.2025_23:55_TELEGRAM_BOT_SUBSCRIBERS.md`

---

**Готово! Теперь все подписчики автоматически сохраняются! 🚀**


