# Модуль 1: Market Research (Исследование рынка)

Автоматический анализ ниш на рынке Казахстана (OLX, Kaspi, Google Trends).

## Функции

- **Парсинг OLX**: Сбор объявлений, цен, конкуренции
- **Парсинг Kaspi**: Анализ товаров и цен на маркетплейсе
- **Google Trends**: Анализ популярности запросов
- **Анализ отзывов**: Парсинг отзывов с 2GIS, Google Maps
- **Оценка ниши**: Расчет потенциала, конкуренции, сезонности

## Установка зависимостей

```bash
pip install scrapy beautifulsoup4 pytrends requests
```

## Использование

### Быстрый запуск

```bash
python modules/1-market-research/main.py --niche "ремонт телефонов" --region "Алматы"
```

### Программное использование

```python
from modules.market_research.parsers.olx_parser import OLXParser

parser = OLXParser()
results = parser.search("ремонт телефонов", city="Алматы")

print(f"Найдено объявлений: {len(results)}")
print(f"Средняя цена: {results['avg_price']} тенге")
```

## Выходные данные

Модуль генерирует JSON-отчет:

```json
{
  "niche": "ремонт телефонов",
  "region": "Алматы",
  "platforms": {
    "olx": {
      "ads_count": 145,
      "avg_price": 5000,
      "competition_level": "medium"
    },
    "kaspi": {
      "products_count": 23,
      "avg_price": 7500
    }
  },
  "trends": {
    "search_volume": 2400,
    "seasonality": "stable"
  },
  "recommendation": "Перспективная ниша с умеренной конкуренцией"
}
```

## Конфигурация

Настройки в `.env`:

```bash
USE_PROXY=True
PROXY_LIST=http://proxy1:port,http://proxy2:port
```

## TODO

- [ ] Добавить парсинг Telegram-каналов
- [ ] Интеграция с Yandex.Wordstat
- [ ] ML-модель для предсказания CPL

