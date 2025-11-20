# Telegram Error Bot - Quick Start

## ⚡ 5-минутный setup

### 1. Создай бота (2 мин)
1. Открой @BotFather в Telegram
2. Отправь `/newbot`
3. Название: `Lead Gen Errors Bot`
4. Username: `leadgen_errors_bot`
5. Сохрани **TOKEN**

### 2. Получи Chat ID (1 мин)
1. Напиши боту `/start`
2. Открой: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Найди `"chat":{"id": 123456789}` ← это твой **CHAT_ID**

### 3. Добавь в .env (30 сек)
```bash
# .env
TELEGRAM_BOT_TOKEN=твой_токен_от_BotFather
TELEGRAM_CHAT_ID=твой_chat_id
```

### 4. Перезапусти сервер (30 сек)
```bash
docker-compose restart backend
```

### 5. Проверь Telegram ✅
Через 10 секунд получишь:
```
✅ Lead Generation System started!
```

**Готово! 🎉**

---

## 📱 Что получаешь:

✅ Мгновенные уведомления о всех ошибках  
✅ Полный stack trace + контекст  
✅ Startup/Shutdown alerts  
✅ Health check мониторинг  
✅ $0/месяц

---

## 🧪 Быстрый тест:

```python
# test_telegram.py
import asyncio
from shared.telegram_notifier import telegram_notifier

async def test():
    await telegram_notifier.send_success("Test!", module="Test")
    
    try:
        raise ValueError("Test error!")
    except Exception as e:
        await telegram_notifier.send_error(e, module="Test")

asyncio.run(test())
```

Запусти:
```bash
python test_telegram.py
```

Проверь Telegram - должно прийти 2 сообщения!

---

**Полный гайд:** `MD/v0.3/19.11.2025_23:45_TELEGRAM_ERROR_BOT_SETUP.md`

