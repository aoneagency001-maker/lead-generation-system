# 🚀 Lead Generation System - Localhost Guide

## Текущий статус

✅ **Система успешно запущена на localhost!**

## 📡 Доступные сервисы

| Сервис | URL | Описание |
|--------|-----|----------|
| **API** | http://localhost:8000 | Основной REST API |
| **Swagger UI** | http://localhost:8000/docs | Интерактивная документация API |
| **ReDoc** | http://localhost:8000/redoc | Альтернативная документация |
| **Health Check** | http://localhost:8000/api/health | Статус сервисов |

## 🛠️ Управление сервером

### Остановить сервер
```bash
cd /Users/vbut/lead-generation-system
./scripts/stop.sh
```

### Перезапустить сервер
```bash
cd /Users/vbut/lead-generation-system
./scripts/restart.sh
```

### Просмотр логов
```bash
cd /Users/vbut/lead-generation-system
tail -f uvicorn.log
```

### Ручной запуск
```bash
cd /Users/vbut/lead-generation-system
source venv/bin/activate
uvicorn core.api.main:app --reload --host 0.0.0.0 --port 8000
```

## ⚙️ Конфигурация

Основные настройки находятся в файле `.env`:

```bash
# Supabase (замените на свои реальные данные!)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Redis
REDIS_URL=redis://localhost:6379/0
```

## 📊 API Endpoints

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Niches (Ниши)
- `GET /api/niches` - Получить все ниши
- `POST /api/niches` - Создать нишу
- `GET /api/niches/{id}` - Получить нишу по ID
- `PUT /api/niches/{id}` - Обновить нишу
- `DELETE /api/niches/{id}` - Удалить нишу

### Campaigns (Кампании)
- `GET /api/campaigns` - Получить все кампании
- `POST /api/campaigns` - Создать кампанию
- `GET /api/campaigns/{id}` - Получить кампанию по ID

### Leads (Лиды)
- `GET /api/leads` - Получить все лиды
- `POST /api/leads` - Создать лид
- `GET /api/leads/{id}` - Получить лид по ID
- `POST /api/leads/{id}/conversations` - Добавить сообщение к лиду

## 🧪 Тестирование API

### Создать нишу
```bash
curl -X POST http://localhost:8000/api/niches \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ремонт ноутбуков",
    "market": "kazakhstan",
    "category": "electronics_repair",
    "description": "Быстрый ремонт ноутбуков всех марок"
  }'
```

### Создать кампанию
```bash
curl -X POST http://localhost:8000/api/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "niche_id": "uuid-здесь",
    "name": "OLX Алматы - Ремонт ноутбуков",
    "platform": "olx",
    "budget": 50000,
    "target_leads": 100
  }'
```

## 📁 Структура проекта

```
/Users/vbut/lead-generation-system/
├── core/
│   ├── api/                    # FastAPI приложение
│   │   ├── main.py            # Точка входа
│   │   ├── config.py          # Конфигурация
│   │   └── routes/            # API endpoints
│   └── database/              # БД схемы и клиенты
│       ├── schema.sql
│       └── supabase_client.py
├── modules/
│   ├── 1-market-research/     # Исследование рынка
│   ├── 2-traffic-generation/  # Генерация трафика
│   ├── 3-lead-qualification/  # Квалификация лидов
│   ├── 4-sales-handoff/       # Передача в продажи
│   └── 5-analytics/           # Аналитика
├── shared/
│   ├── utils.py               # Утилиты
│   └── models.py              # Pydantic модели
├── scripts/
│   ├── restart.sh             # Перезапуск
│   ├── stop.sh                # Остановка
│   └── setup_database.py      # Настройка БД
├── .env                       # Переменные окружения
├── requirements.txt           # Python зависимости
└── docker-compose.yml         # Docker конфигурация

```

## 🚨 Решение проблем

### Порт 8000 уже занят
```bash
# Найти процесс
lsof -i :8000

# Убить процесс
kill -9 <PID>
```

### Ошибки импорта модулей
```bash
cd /Users/vbut/lead-generation-system
source venv/bin/activate
pip install -r requirements.txt
```

### Ошибки БД (Supabase)
1. Зарегистрируйтесь на https://supabase.com
2. Создайте новый проект
3. Скопируйте URL и anon key
4. Обновите `.env` файл
5. Запустите `python scripts/setup_database.py`

## 📚 Следующие шаги

1. **Настроить Supabase**
   - Создать проект на supabase.com
   - Обновить `.env` с реальными credentials
   - Запустить `python scripts/setup_database.py`

2. **Установить Redis** (опционально)
   ```bash
   brew install redis
   redis-server
   ```

3. **Настроить Telegram Bot**
   - Создать бота через @BotFather
   - Добавить токен в `.env`

4. **Настроить WhatsApp**
   - Установить WAHA: https://waha.devlike.pro/
   - Обновить `.env`

5. **Развернуть на VPS**
   - Следовать инструкциям в `QUICKSTART.md`

## 📞 Поддержка

- Документация API: http://localhost:8000/docs
- Проект: /Users/vbut/lead-generation-system
- Логи: `tail -f uvicorn.log`

---
**Версия:** 0.0 Demo  
**Дата:** 2024-11-16  
**Статус:** ✅ Работает

