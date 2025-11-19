# Competitor Parser Module

Модуль парсинга сайтов конкурентов для извлечения товаров, цен и SEO данных.

## 🎯 Возможности

- **Универсальный парсер** - парсинг любых сайтов с авто-детекцией структуры
- **Специфичные парсеры** - оптимизированные парсеры для Satu.kz, Kaspi.kz
- **SEO данные** - извлечение meta-тегов, заголовков, schema.org
- **Множество форматов экспорта** - JSON, CSV, SQL, WordPress XML
- **Background tasks** - асинхронный парсинг в фоне
- **Event Bus** - интеграция с будущими модулями (SEO Analyzer, Content Generator)

## 📦 Структура

```
modules/competitor-parser/
├── __init__.py              # Экспорт основных классов
├── models.py                # Pydantic модели
├── config.py                # Настройки
├── api/
│   ├── routes.py            # FastAPI endpoints
│   └── __init__.py
├── database/
│   ├── schema.sql           # SQL схема
│   ├── client.py            # Database client
│   ├── apply_schema.py      # Скрипт применения схемы
│   └── __init__.py
├── parsers/
│   ├── base_parser.py       # Базовый класс
│   ├── universal_parser.py  # Универсальный парсер (Playwright)
│   ├── satu_parser.py       # Satu.kz парсер
│   ├── configs/
│   │   ├── satu_config.py   # Конфигурация Satu.kz
│   │   └── __init__.py
│   └── __init__.py
├── services/
│   ├── parser_service.py    # Бизнес-логика парсинга
│   ├── export_service.py    # Экспорт данных
│   └── __init__.py
├── README.md                # Этот файл
└── TEST_GUIDE.md            # Гайд по тестированию
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
cd /path/to/lead-generation-system

# Активировать venv
source venv/bin/activate

# Установить Playwright браузеры
python -m playwright install chromium
```

### 2. Применение схемы БД

Откройте Supabase Dashboard → SQL Editor и выполните:
```bash
modules/competitor-parser/database/schema.sql
```

Или используйте скрипт:
```bash
python modules/competitor-parser/database/apply_schema.py
```

### 3. Настройка переменных окружения

В `.env` должны быть:
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_key_here
```

### 4. Запуск API

```bash
uvicorn core.api.main:app --reload
```

API доступен на http://localhost:8000/docs

### 5. Использование

#### Через API

```bash
# Запустить парсинг
curl -X POST "http://localhost:8000/api/parser/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://satu.kz/example",
    "parser_type": "satu",
    "max_pages": 1
  }'

# Получить статус
curl "http://localhost:8000/api/parser/tasks/TASK_ID"

# Экспорт
curl "http://localhost:8000/api/parser/export/json?task_id=TASK_ID" -o products.json
```

#### Через Python

```python
import asyncio
from modules.competitor_parser.parsers.satu_parser import SatuParser

async def parse_example():
    async with SatuParser() as parser:
        product = await parser.parse_product_page("https://satu.kz/...")
        
        if product:
            print(f"Title: {product.title}")
            print(f"Price: {product.price.amount if product.price else 'N/A'}")
            print(f"Images: {len(product.images)}")

asyncio.run(parse_example())
```

#### Через Frontend

1. Откройте http://localhost:3000/dashboard/parser
2. Введите URL товара или категории
3. Выберите тип парсера
4. Нажмите "Запустить парсинг"
5. Экспортируйте результаты в нужном формате

## 📋 API Endpoints

### Парсинг

- `POST /api/parser/parse` - Запустить парсинг
- `GET /api/parser/tasks/{id}` - Статус задачи
- `GET /api/parser/tasks` - Список последних задач

### Данные

- `GET /api/parser/products` - Получить товары
- `GET /api/parser/products/{id}` - Получить товар по ID
- `GET /api/parser/statistics` - Общая статистика

### Экспорт

- `GET /api/parser/export/json` - Экспорт в JSON
- `GET /api/parser/export/csv` - Экспорт в CSV
- `GET /api/parser/export/sql` - Экспорт в SQL
- `GET /api/parser/export/wordpress_xml` - Экспорт в WordPress XML
- `GET /api/parser/export/schema_org` - Экспорт в Schema.org JSON-LD

### Утилиты

- `GET /api/parser/health` - Health check

## 🎛️ Конфигурация

### Parser Settings

В `config.py`:

```python
class CompetitorParserSettings(BaseSettings):
    default_parser_type: str = "universal"
    default_rate_limit: float = 2.0  # секунд между запросами
    max_concurrent_parsers: int = 3
    playwright_headless: bool = True
    save_raw_html: bool = False  # Сохранять HTML для отладки
```

### Добавление нового сайта

1. Создайте конфигурацию в `parsers/configs/`:

```python
# parsers/configs/example_config.py
from ...models import ParserConfig, ParserType

EXAMPLE_CONFIG = ParserConfig(
    site_name="example.com",
    base_url="https://example.com",
    parser_type=ParserType.CUSTOM,
    use_playwright=True,
    selectors={
        "title": "h1.product-title",
        "price": ".price-amount",
        "images": ".gallery img",
        # ... другие селекторы
    },
    rate_limit=2.0
)
```

2. Создайте парсер (опционально):

```python
# parsers/example_parser.py
from .universal_parser import UniversalParser
from .configs.example_config import EXAMPLE_CONFIG

class ExampleParser(UniversalParser):
    def __init__(self):
        super().__init__(config=EXAMPLE_CONFIG)
```

3. Добавьте в `parser_service.py`:

```python
def _create_parser(self, parser_type: ParserType):
    if parser_type == ParserType.EXAMPLE:
        return ExampleParser()
    # ...
```

## 📊 Форматы экспорта

### JSON
Полная структура данных с вложенными объектами.

### CSV
Таблица с основными полями товаров.

### SQL
INSERT statements для импорта в любую PostgreSQL БД.

### WordPress XML (WXR)
Готовый импорт в WordPress для ПБН сайтов. Включает:
- Посты с контентом
- Custom fields (цена, SKU)
- Категории
- Изображения

### Schema.org JSON-LD
Структурированные данные для SEO.

## 🔄 Event Bus Integration

Модуль отправляет события для будущих модулей:

```python
# После завершения парсинга
emit_event("parser.completed", {
    "task_id": "...",
    "url": "...",
    "products_count": 10,
    "duration": 15.5
})
```

Подписка на события:

```python
from shared.event_bus import subscribe_to_event

def on_parser_completed(data):
    print(f"Parsing completed: {data['products_count']} products")

subscribe_to_event("parser.completed", on_parser_completed)
```

## 🏗️ Roadmap

### Текущая итерация (MVP)
- ✅ Универсальный парсер
- ✅ Satu.kz парсер
- ✅ API endpoints
- ✅ Export в JSON/CSV/SQL/WordPress XML
- ✅ Frontend UI

### Итерация 2: SEO Analyzer Module
- Глубокий SEO-анализ страниц
- Извлечение LSI keywords
- Анализ конкурентов
- Core Web Vitals

### Итерация 3: Content Generator Module
- AI-генерация уникального контента
- Спинтакс для вариаций
- SEO-оптимизация текстов

### Итерация 4: PBN Manager Module
- Управление ПБН сайтами
- Автопостинг через WordPress API
- Управление перелинковкой

### Итерация 5: Money Site Manager
- Импорт на основной сайт
- A/B тестирование
- Мониторинг позиций

## 🧪 Тестирование

Полный гайд: [TEST_GUIDE.md](TEST_GUIDE.md)

Быстрый тест:

```bash
# Health check
curl http://localhost:8000/api/parser/health

# Запустить тестовый парсинг
curl -X POST "http://localhost:8000/api/parser/parse" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://satu.kz/...", "parser_type": "satu"}'
```

## 📝 Логирование

Логи доступны в:
- `uvicorn.log` - общие логи API
- Console output при `--reload`

Настройка уровня логов в `.env`:
```env
LOG_LEVEL=INFO
```

## 🛡️ Безопасность

- Rate limiting (2 сек между запросами по умолчанию)
- User-Agent rotation
- Respect robots.txt (опционально)
- Только публичные данные

## 🤝 Contributing

При добавлении нового парсера:

1. Следуйте паттерну существующих парсеров
2. Добавьте type hints
3. Добавьте логирование
4. Обработайте ошибки
5. Добавьте тесты
6. Обновите документацию

## 📄 License

GPL-3.0 License - см. основной README проекта.

## 🔗 Связанные модули

- `shared/event_bus.py` - Event Bus для интеграции
- `core/database/supabase_client.py` - Database client
- `frontend/app/(dashboard)/dashboard/parser/` - Frontend UI

## 📧 Support

При возникновении проблем:

1. Проверьте [TEST_GUIDE.md](TEST_GUIDE.md)
2. Посмотрите логи
3. Проверьте применение schema.sql
4. Убедитесь что Playwright установлен

---

**Version:** 0.1.0  
**Status:** MVP Ready  
**Last Updated:** 2025-11-18

