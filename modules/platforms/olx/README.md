# OLX.kz Autonomous Module

Автономный модуль для работы с платформой OLX.kz.

## Возможности

### Авторизация
- **OAuth 2.0** - через официальный OLX Partner API
- **Playwright Browser** - эмуляция браузера с anti-detect

### Парсинг
- **lerdem/olx-parser** - адаптированный open-source парсер
- **Playwright Parser** - парсинг через браузер
- **Official API** - через Partner API (если доступно)

### Публикация объявлений
- **API Publisher** - через официальный API
- **Browser Publisher** - через Playwright автоматизацию

## Быстрый старт

### 1. Установка зависимостей

```bash
cd modules/platforms/olx
pip install -r requirements.txt
playwright install chromium
```

### 2. Настройка окружения

Создайте `.env` файл на основе `.env.example`:

```bash
cp .env.example .env
```

Заполните необходимые переменные:
- `SUPABASE_URL` и `SUPABASE_KEY`
- `OLX_CLIENT_ID` и `OLX_CLIENT_SECRET` (для OAuth)
- Redis URL

### 3. Применение схемы БД

```bash
# Выполните SQL из database/schema.sql в Supabase
```

### 4. Запуск модуля

```bash
# Через uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload

# Или через Docker
docker-compose up -d
```

### 5. Проверка

```bash
curl http://localhost:8001/health
# {"status": "healthy", "module": "olx"}
```

## API Documentation

После запуска доступна по адресу: http://localhost:8001/docs

### Основные endpoints:

#### Авторизация
- `POST /auth/oauth/login` - OAuth авторизация
- `POST /auth/browser/login` - Browser авторизация
- `GET /auth/accounts` - Список аккаунтов
- `GET /auth/accounts/{id}` - Информация об аккаунте

#### Объявления
- `POST /ads` - Создать объявление
- `GET /ads` - Список объявлений
- `GET /ads/{id}` - Информация об объявлении
- `PUT /ads/{id}` - Обновить объявление
- `DELETE /ads/{id}` - Удалить объявление

#### Парсинг
- `POST /parser/search` - Запустить парсинг
- `GET /parser/tasks/{id}` - Статус задачи
- `GET /parser/results/{id}` - Результаты парсинга

## SDK Usage

```python
from modules.platforms.olx.sdk import OLXClient

# Инициализация клиента
client = OLXClient(base_url="http://localhost:8001")

# OAuth авторизация
account = await client.login_oauth(
    email="your@email.com",
    password="password",
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# Парсинг
results = await client.parse_search(
    query="iphone",
    city="almaty",
    method="playwright"
)

# Публикация
ad = await client.create_ad(
    account_id=account.id,
    title="iPhone 15 Pro",
    description="Новый телефон",
    price=500000,
    city="Алматы",
    images=["https://example.com/image.jpg"]
)
```

## Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `OLX_SUPABASE_URL` | URL Supabase | - (обязательно) |
| `OLX_SUPABASE_KEY` | Supabase API Key | - (обязательно) |
| `OLX_CLIENT_ID` | OLX API Client ID | None |
| `OLX_CLIENT_SECRET` | OLX API Client Secret | None |
| `OLX_MODULE_PORT` | Порт модуля | 8001 |
| `OLX_REDIS_URL` | Redis URL | redis://localhost:6379/1 |
| `OLX_BROWSER_HEADLESS` | Headless режим | true |
| `OLX_USE_PROXY` | Использовать прокси | false |
| `OLX_PROXY_URL` | URL прокси | None |

## Структура

```
olx/
├── api/                    # FastAPI приложение
│   ├── main.py            # Entry point
│   ├── config.py          # Настройки
│   └── routes/            # API endpoints
│       ├── auth.py
│       ├── ads.py
│       └── parser.py
├── database/
│   ├── schema.sql         # SQL схема
│   └── client.py          # Supabase client
├── models.py              # Pydantic модели
├── services/              # Бизнес-логика
│   ├── auth_service.py
│   ├── parser_service.py
│   └── publisher_service.py
├── sdk/                   # SDK для интеграции
│   └── __init__.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Тестирование

### Unit tests

```bash
pytest tests/
```

### Integration tests

```bash
pytest tests/integration/
```

## Деплой

### Docker

```bash
docker-compose up -d
```

### VPS

```bash
# 1. Клонировать репозиторий
git clone <repo> /opt/olx-module

# 2. Создать .env
cp .env.example .env
nano .env

# 3. Запустить через systemd или supervisor
```

## Лицензия

Проприетарная - часть Lead Generation System

## Автор

Lead Generation System Team



