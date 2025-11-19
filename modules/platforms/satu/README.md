# Satu.kz Autonomous Module

Автономный модуль для работы с платформой Satu.kz.

## Возможности

### Авторизация
- **API Token** - через официальный Satu.kz API
- **Playwright Browser** - эмуляция браузера (fallback)

### Парсинг
- **Playwright Parser** - парсинг через браузер
- **Official API** - через Satu.kz API (если доступно)

### Публикация товаров
- **API Publisher** - через официальный API
- **Browser Publisher** - через Playwright (fallback)

### Управление заказами
- Получение заказов через API
- Обновление статусов
- Работа с сообщениями от клиентов

## Быстрый старт

### 1. Установка зависимостей

```bash
cd modules/platforms/satu
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
- Redis URL

### 3. Получение API токена Satu.kz

1. Войдите в ваш аккаунт на satu.kz
2. Перейдите в **Настройки → Управление API-токенами**
3. Создайте новый токен с правами: Orders, Products, Groups, Clients
4. Скопируйте токен в `.env` файл

### 4. Применение схемы БД

```bash
# Выполните SQL из database/schema.sql в Supabase
```

### 5. Запуск модуля

```bash
# Через uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8002 --reload

# Или через Docker
docker-compose up -d
```

### 6. Проверка

```bash
curl http://localhost:8002/health
# {"status": "healthy", "module": "satu"}
```

## API Documentation

После запуска доступна по адресу: http://localhost:8002/docs

### Основные endpoints:

#### Авторизация
- `POST /auth/token` - Добавить API токен
- `GET /auth/accounts` - Список аккаунтов
- `GET /auth/accounts/{id}` - Информация об аккаунте

#### Товары
- `POST /products` - Создать товар
- `GET /products` - Список товаров
- `GET /products/{id}` - Информация о товаре
- `PUT /products/{id}` - Обновить товар
- `DELETE /products/{id}` - Удалить товар

#### Заказы
- `GET /orders` - Список заказов
- `GET /orders/{id}` - Информация о заказе
- `PUT /orders/{id}/status` - Обновить статус заказа

#### Парсинг
- `POST /parser/search` - Запустить парсинг
- `GET /parser/tasks/{id}` - Статус задачи
- `GET /parser/results/{id}` - Результаты парсинга

## SDK Usage

```python
from modules.platforms.satu.sdk import SatuClient

# Инициализация клиента
client = SatuClient(base_url="http://localhost:8002")

# Добавление API токена
account = await client.add_token(
    company_name="Моя компания",
    api_token="your_api_token"
)

# Парсинг
results = await client.parse_search(
    query="телефоны",
    method="playwright"
)

# Публикация товара
product = await client.create_product(
    account_id=account.id,
    title="iPhone 15 Pro",
    description="Новый телефон",
    price=500000,
    stock_quantity=10,
    images=["https://example.com/image.jpg"]
)

# Получение заказов
orders = await client.get_orders(account_id=account.id)
```

## Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `SATU_SUPABASE_URL` | URL Supabase | - (обязательно) |
| `SATU_SUPABASE_KEY` | Supabase API Key | - (обязательно) |
| `SATU_MODULE_PORT` | Порт модуля | 8002 |
| `SATU_REDIS_URL` | Redis URL | redis://localhost:6379/2 |
| `SATU_BROWSER_HEADLESS` | Headless режим | true |
| `SATU_USE_PROXY` | Использовать прокси | false |
| `SATU_PROXY_URL` | URL прокси | None |

## Структура

```
satu/
├── api/                    # FastAPI приложение
│   ├── main.py            # Entry point
│   ├── config.py          # Настройки
│   └── routes/            # API endpoints
│       ├── auth.py
│       ├── products.py
│       ├── orders.py
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

## Работа с Satu.kz API

### Получение токена

1. Авторизуйтесь на satu.kz
2. Настройки → Управление API-токенами
3. Создайте токен с правами:
   - Orders (чтение и запись)
   - Products (чтение и запись)
   - Groups (чтение)
   - Clients (чтение)

### Права доступа

- **Нет доступа**: 403 Forbidden
- **Только чтение**: GET = 200 OK, POST = 403 Forbidden
- **Чтение и запись**: GET и POST = 200 OK

### Коды ошибок

- **401 Not Authenticated**: Токен истёк или невалидный
- **403 Forbidden**: Нет прав на операцию
- **404 Not Found**: Ресурс не найден
- **429 Too Many Requests**: Превышен лимит запросов

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
git clone <repo> /opt/satu-module

# 2. Создать .env
cp .env.example .env
nano .env

# 3. Запустить через systemd или supervisor
```

## Лицензия

Проприетарная - часть Lead Generation System

## Автор

Lead Generation System Team


