# Competitor Parser Module - Test Guide

## Тестирование модуля парсинга конкурентов

Этот гайд описывает шаги для полного тестирования модуля.

## Предварительные требования

1. ✅ PostgreSQL (Supabase) с примененной схемой
2. ✅ Python 3.9+ с установленными зависимостями
3. ✅ Playwright браузер установлен
4. ✅ Переменные окружения настроены (.env)

## Шаг 1: Применение схемы БД

```bash
cd /Users/vbut/lead-generation-system

# Активировать venv
source venv/bin/activate

# Применить схему (вручную через Supabase Dashboard)
# Откройте Supabase Dashboard → SQL Editor
# Скопируйте и выполните: modules/competitor-parser/database/schema.sql
```

## Шаг 2: Установка Playwright браузеров

```bash
# Установить браузеры для Playwright
python -m playwright install chromium
```

## Шаг 3: Запуск Backend API

```bash
cd /Users/vbut/lead-generation-system

# Активировать venv если не активирован
source venv/bin/activate

# Запустить API
uvicorn core.api.main:app --reload --host 0.0.0.0 --port 8000
```

API должен быть доступен на http://localhost:8000

## Шаг 4: Проверка API через Swagger

1. Откройте http://localhost:8000/docs
2. Найдите секцию "Competitor Parser"
3. Проверьте доступность endpoints:
   - `POST /api/parser/parse`
   - `GET /api/parser/tasks/{task_id}`
   - `GET /api/parser/products`
   - `GET /api/parser/export/{format}`
   - `GET /api/parser/health`

### Тест 1: Health Check

```bash
curl http://localhost:8000/api/parser/health
```

Ожидаемый ответ:
```json
{
  "status": "healthy",
  "module": "competitor-parser",
  "version": "0.1.0"
}
```

### Тест 2: Запуск парсинга

```bash
curl -X POST "http://localhost:8000/api/parser/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://satu.kz/example-product",
    "parser_type": "satu",
    "max_pages": 1
  }'
```

Ожидаемый ответ:
```json
{
  "success": true,
  "task_id": "uuid-here",
  "status": "pending",
  "message": "Parsing task created. Type: satu"
}
```

### Тест 3: Проверка статуса задачи

```bash
# Замените TASK_ID на реальный ID из предыдущего шага
curl http://localhost:8000/api/parser/tasks/TASK_ID
```

### Тест 4: Получение товаров

```bash
curl "http://localhost:8000/api/parser/products?limit=10"
```

### Тест 5: Экспорт данных

```bash
# JSON
curl "http://localhost:8000/api/parser/export/json?task_id=TASK_ID" -o products.json

# CSV
curl "http://localhost:8000/api/parser/export/csv?task_id=TASK_ID" -o products.csv

# WordPress XML
curl "http://localhost:8000/api/parser/export/wordpress_xml?task_id=TASK_ID" -o products.xml
```

## Шаг 5: Запуск Frontend

```bash
cd /Users/vbut/lead-generation-system/frontend

# Установить зависимости (если еще не установлены)
npm install

# Запустить dev server
npm run dev
```

Frontend должен быть доступен на http://localhost:3000

## Шаг 6: Тестирование UI

1. Откройте http://localhost:3000/dashboard/parser
2. Проверьте отображение статистики
3. Введите тестовый URL (например: https://satu.kz/...)
4. Выберите тип парсера (Satu.kz)
5. Нажмите "Запустить парсинг"
6. Проверьте:
   - ✅ Отображение прогресс-бара
   - ✅ Обновление статуса в реальном времени
   - ✅ Появление товаров в таблице
   - ✅ Работу кнопок экспорта

## Шаг 7: Тестирование парсеров

### Тест универсального парсера

```python
import asyncio
from modules.competitor_parser.parsers.universal_parser import UniversalParser

async def test_universal():
    async with UniversalParser() as parser:
        # Замените на реальный URL
        product = await parser.parse_product_page("https://example.com/product/123")
        
        if product:
            print(f"✅ Parsed: {product.title}")
            print(f"   Price: {product.price.amount if product.price else 'N/A'}")
            print(f"   Images: {len(product.images)}")
        else:
            print("❌ Failed to parse")

asyncio.run(test_universal())
```

### Тест Satu.kz парсера

```python
import asyncio
from modules.competitor_parser.parsers.satu_parser import SatuParser

async def test_satu():
    async with SatuParser() as parser:
        # Замените на реальный URL с Satu.kz
        product = await parser.parse_product_page("https://satu.kz/...")
        
        if product:
            print(f"✅ Parsed: {product.title}")
            print(f"   SKU: {product.sku}")
            print(f"   Category: {product.category}")
            print(f"   Attributes: {len(product.attributes)}")
        else:
            print("❌ Failed to parse")

asyncio.run(test_satu())
```

## Шаг 8: Проверка базы данных

```sql
-- Проверить таблицы
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('parser_tasks', 'parsed_products', 'parsed_sites');

-- Проверить задачи
SELECT id, url, parser_type, status, products_found 
FROM parser_tasks 
ORDER BY created_at DESC 
LIMIT 10;

-- Проверить товары
SELECT id, title, sku, price_amount, source_site 
FROM parsed_products 
ORDER BY parsed_at DESC 
LIMIT 10;

-- Статистика
SELECT 
  source_site,
  COUNT(*) as total_products,
  AVG(price_amount) as avg_price
FROM parsed_products
GROUP BY source_site;
```

## Шаг 9: Event Bus интеграция (опционально)

Проверить что события корректно отправляются:

```python
# В shared/event_bus.py должно быть:
from shared.event_bus import subscribe_to_event

def on_parser_completed(data):
    print(f"Parser completed event: {data}")

subscribe_to_event("parser.completed", on_parser_completed)
```

## Критерии успешного теста

- [ ] ✅ API health check работает
- [ ] ✅ Задача парсинга создается
- [ ] ✅ Статус задачи обновляется
- [ ] ✅ Товары сохраняются в БД
- [ ] ✅ Экспорт в разных форматах работает
- [ ] ✅ Frontend отображается корректно
- [ ] ✅ Парсинг через UI работает
- [ ] ✅ Таблицы в БД созданы
- [ ] ✅ События отправляются (опционально)

## Troubleshooting

### Проблема: Playwright браузер не найден

```bash
python -m playwright install chromium
```

### Проблема: Таблицы не существуют

Примените schema.sql через Supabase Dashboard SQL Editor.

### Проблема: Import errors

```bash
# Убедитесь что venv активирован
source venv/bin/activate

# Переустановите зависимости
pip install -r requirements.txt
```

### Проблема: CORS errors в frontend

Проверьте что backend запущен и CORS настроен правильно в `core/api/main.py`.

### Проблема: Парсинг не работает

1. Проверьте доступность сайта
2. Проверьте селекторы в конфигурации
3. Посмотрите логи: `tail -f uvicorn.log`

## Дополнительная информация

- **Документация API:** http://localhost:8000/docs
- **Логи backend:** `uvicorn.log`
- **Схема БД:** `modules/competitor-parser/database/schema.sql`
- **Конфигурации парсеров:** `modules/competitor-parser/parsers/configs/`

## Следующие шаги

После успешного тестирования:

1. Добавить больше конфигураций для других сайтов
2. Настроить event bus для SEO Analyzer (будущая итерация)
3. Создать scheduled tasks для регулярного парсинга
4. Добавить webhook уведомления
5. Настроить мониторинг и alerting

