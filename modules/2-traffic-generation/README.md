# Модуль 2: Traffic Generation (Генерация трафика)

Автоматическая публикация объявлений на OLX, Kaspi, Telegram.

## Функции

- **OLX автопостинг**: Playwright-автоматизация публикации
- **Kaspi интеграция**: Загрузка товаров через API/автоматизацию
- **Telegram посев**: Публикация в каналах и группах через Telethon
- **Антидетект**: Обход капчи, ротация прокси, маскировка браузера

## Установка

```bash
pip install playwright telethon 2captcha-python
playwright install chromium
```

## Использование

### Публикация на OLX

```bash
python modules/2-traffic-generation/publishers/olx_publisher.py \
  --title "Ремонт iPhone" \
  --price 5000 \
  --description "Быстрый ремонт" \
  --category "services"
```

### Программное использование

```python
from modules.traffic_generation.publishers.olx_publisher import OLXPublisher

publisher = OLXPublisher(
    email="your@email.com",
    password="password"
)

ad_id = publisher.create_ad(
    title="Ремонт iPhone",
    price=5000,
    description="Быстрый ремонт телефонов",
    images=["photo1.jpg", "photo2.jpg"]
)

print(f"Объявление создано: {ad_id}")
```

## ⚠️ Важные предупреждения

1. **Риск блокировки**: OLX/Kaspi активно банят автоматизацию
2. **Прокси обязательны**: Используйте мобильные прокси КЗ
3. **Лимиты**: Не более 5-10 объявлений в день с одного аккаунта
4. **Прогрев аккаунтов**: Новые аккаунты публикуют меньше

## Конфигурация

```bash
# .env
OLX_EMAIL_1=your@email.com
OLX_PASSWORD_1=password
OLX_PHONE_1=+77001234567

CAPTCHA_API_KEY=your-2captcha-key
USE_PROXY=True
PROXY_LIST=mobile-proxy-kz:port
```

## TODO

- [ ] Автоматическое обновление объявлений
- [ ] Мониторинг статуса (активно/забанено)
- [ ] A/B тестирование заголовков

