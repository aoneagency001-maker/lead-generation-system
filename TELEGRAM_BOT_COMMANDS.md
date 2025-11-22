# 🤖 Telegram Bot - Команды

## ⚡ Быстрый старт

### 1. Запусти бота
```bash
python -m shared.telegram_bot
# или
./scripts/start_telegram_bot.sh
```

### 2. Отправь команды в Telegram

```
/start   - Приветствие
/status  - Статус системы
/health  - Health check
/stats   - Статистика (24h)
/help    - Справка
```

---

## 🧪 Тестирование

### Полный тест всех функций:
```bash
python scripts/test_telegram_bot.py
```

**Что тестируется:**
- ✅ Все типы уведомлений (success, error, warning, critical)
- ✅ Все команды бота
- ✅ Error handling

**Проверь Telegram** - должно прийти 10+ сообщений!

---

## 📱 Примеры команд

### `/status`
```
📊 System Status

🟢 Status: Running
🗄️ Database: ✅ OK
🌍 Environment: Development
```

### `/health`
```
🏥 Health Check

Overall Status: ✅ Healthy

Services:
• Database: ✅ OK
• Telegram: ✅ Configured
```

### `/stats`
```
📈 Statistics (Last 24h)

👥 Leads created: 42
🚀 Active campaigns: 3
❌ Errors: 0
```

---

## 🔧 Использование в коде

```python
from shared.telegram_notifier import notify_success, notify_error

# Успех
await notify_success("Lead created!", module="LeadService")

# Ошибка
try:
    result = await risky_operation()
except Exception as e:
    await notify_error(e, module="MyService")
    raise
```

---

## 📚 Документация

**Полный гайд:** `MD/v0.3/19.11.2025_23:50_TELEGRAM_BOT_COMMANDS.md`

**Quick Start:** `TELEGRAM_BOT_QUICKSTART.md`

---

**Готово! Отправь `/start` боту и начни использовать! 🚀**


