# ⚙️ Configuration Guide - Lead Generation System

Полное руководство по настройке системы через переменные окружения.

---

## 📁 Файл .env

Все настройки хранятся в файле `.env` в корне проекта. Создайте его на основе `.env.example`.

```bash
cp .env.example .env
```

---

## 🔑 Обязательные настройки

### Supabase (База данных)

```bash
# URL вашего Supabase проекта
SUPABASE_URL=https://your-project.supabase.co

# Anon/public key (для клиентских запросов)
SUPABASE_KEY=your_anon_key_here

# Service role key (для админских операций, опционально)
SUPABASE_SERVICE_KEY=your_service_key_here
```

**Как получить:**
1. Зайдите на https://supabase.com/dashboard
2. Выберите ваш проект
3. Settings → API
4. Скопируйте URL и ключи

---

## 🤖 API Settings

```bash
# Хост и порт для FastAPI
API_HOST=0.0.0.0
API_PORT=8000

# Режим отладки (true для разработки)
DEBUG=true

# Секретный ключ для API (измените в production!)
API_SECRET_KEY=change-me-in-production
```

---

## 📦 Redis

```bash
# URL подключения к Redis
REDIS_URL=redis://localhost:6379/0
```

**Для production:**
```bash
REDIS_URL=redis://user:password@redis-host:6379/0
```

---

## 📱 Telegram

```bash
# Токен бота (получить у @BotFather)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Chat ID для уведомлений (получить у @userinfobot)
TELEGRAM_NOTIFICATION_CHAT_ID=123456789

# Chat ID для продаж (опционально)
TELEGRAM_SALES_CHAT_ID=987654321
```

**Как получить токен:**
1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен

---

## 💬 WhatsApp (WAHA)

```bash
# URL WAHA API (если используете)
WHATSAPP_API_URL=http://localhost:3001
WHATSAPP_API_KEY=your_api_key_here
WHATSAPP_SESSION_NAME=leadgen
```

---

## 🔄 n8n

```bash
# URL n8n (локально или удаленно)
N8N_URL=http://localhost:5678

# API ключ (опционально)
N8N_API_KEY=your_n8n_api_key
```

---

## 🌐 Proxy (для скрапинга)

```bash
# Использовать прокси
USE_PROXY=false
PROXY_ENABLED=false

# Тип прокси
PROXY_TYPE=http  # http, socks5

# Один прокси
PROXY_HOST=proxy.example.com
PROXY_PORT=8080
PROXY_USERNAME=user
PROXY_PASSWORD=pass

# Или список прокси (через запятую)
PROXY_LIST=http://user:pass@proxy1.com:8080,http://user:pass@proxy2.com:8080

# Или полный URL
PROXY_URL=http://user:pass@proxy.example.com:8080

# Интервал ротации (секунды)
PROXY_ROTATION_INTERVAL=300
```

**Для Казахстана рекомендуется:**
- Мобильные прокси с IP из Казахстана
- Ротация каждые 5-10 минут
- Разные прокси для разных платформ

---

## 🧩 CAPTCHA Solving

```bash
# API ключ 2Captcha
CAPTCHA_API_KEY=your_2captcha_api_key
CAPTCHA_ENABLED=true
```

**Как получить:**
1. Зарегистрируйтесь на https://2captcha.com
2. Пополните баланс ($5-10 для теста)
3. Скопируйте API key из личного кабинета

---

## 🤖 AI/LLM

### OpenAI

```bash
# API ключ OpenAI
OPENAI_API_KEY=sk-...

# Модель (gpt-4, gpt-4-turbo, gpt-3.5-turbo)
OPENAI_MODEL=gpt-4

# Максимальное количество токенов
OPENAI_MAX_TOKENS=500
```

### Anthropic (Claude)

```bash
# API ключ Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Модель
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### Ollama (локальный LLM)

```bash
# Использовать локальный LLM
USE_LOCAL_LLM=false

# URL Ollama
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 🛒 OLX

```bash
# Аккаунты OLX (можно несколько)
OLX_EMAIL_1=your-email@example.com
OLX_PASSWORD_1=your-password
OLX_PHONE_1=+7 777 123 4567
```

**Важно:** Храните пароли в безопасности! В production используйте секреты.

---

## 💳 Kaspi

```bash
# Merchant ID
KASPI_MERCHANT_ID=your_merchant_id

# API ключ
KASPI_API_KEY=your_kaspi_api_key
```

---

## 📧 Email (для уведомлений)

```bash
# SMTP настройки
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

**Для Gmail:**
1. Включите двухфакторную аутентификацию
2. Создайте App Password
3. Используйте его как `EMAIL_PASSWORD`

---

## 📱 SMS (Twilio)

```bash
# Провайдер SMS
SMS_PROVIDER=twilio

# Twilio credentials
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

---

## 📊 Настройки модулей

### Module 1: Market Research

```bash
# Максимальное количество воркеров для скрапинга
MAX_SCRAPING_WORKERS=3

# Лимит запросов в секунду
SCRAPING_RATE_LIMIT=1

# Таймаут запросов (секунды)
SCRAPING_TIMEOUT=30
```

### Module 2: Traffic Generation

```bash
# Максимальное количество объявлений в день
MAX_ADS_PER_DAY=10

# Максимальное количество объявлений на кампанию
MAX_ADS_PER_CAMPAIGN=10

# Задержка между публикациями (секунды)
AD_POSTING_DELAY_MIN=2
AD_POSTING_DELAY_MAX=5
```

### Module 3: Lead Qualification

```bash
# Минимальный score для квалификации
MIN_QUALIFICATION_SCORE=60

# Таймаут квалификации (секунды)
LEAD_QUALIFICATION_TIMEOUT=300
```

### Module 4: Sales Handoff

```bash
# Порог для автоматической передачи
AUTO_HANDOFF_THRESHOLD=80

# Каналы уведомлений (через запятую)
HANDOFF_NOTIFICATION_CHANNELS=telegram,email
```

### Module 5: Analytics

```bash
# TTL кэша метрик (секунды)
METRICS_CACHE_TTL=3600

# Время ежедневного отчета (HH:MM)
DAILY_REPORT_TIME=09:00

# Включить ежедневные отчеты
ENABLE_DAILY_REPORTS=true
```

---

## 🔔 Уведомления

```bash
# Включить уведомления
ENABLE_NOTIFICATIONS=true

# Каналы уведомлений (через запятую)
NOTIFICATION_CHANNELS=telegram,email
```

---

## 📝 Логирование

```bash
# Уровень логирования (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Файл логов
LOG_FILE=logs/app.log
```

---

## 🔍 Аналитика

```bash
# Google Analytics (опционально)
GA_TRACKING_ID=UA-XXXXX-Y

# Sentry для отслеживания ошибок (опционально)
SENTRY_DSN=https://xxx@sentry.io/xxx
```

---

## 🚀 Production настройки

### Безопасность

```bash
# Обязательно измените в production!
API_SECRET_KEY=strong-random-secret-key-here

# Отключите debug
DEBUG=false

# Ограничьте CORS
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### Производительность

```bash
# Увеличьте лимиты для production
MAX_SCRAPING_WORKERS=10
MAX_ADS_PER_DAY=50
METRICS_CACHE_TTL=7200
```

### Мониторинг

```bash
# Включите Sentry
SENTRY_DSN=https://xxx@sentry.io/xxx

# Настройте логирование
LOG_LEVEL=INFO
LOG_FILE=/var/log/leadgen/app.log
```

---

## ✅ Проверка конфигурации

После настройки `.env` проверьте конфигурацию:

```bash
python scripts/test_connection.py
```

Этот скрипт проверит:
- ✅ Подключение к Supabase
- ✅ Подключение к Redis
- ✅ Валидность Telegram токена
- ✅ Доступность других сервисов

---

## 🔐 Безопасность

### ⚠️ НИКОГДА не коммитьте .env в Git!

Убедитесь, что `.env` в `.gitignore`:

```gitignore
.env
.env.local
.env.*.local
```

### Рекомендации:

1. **Используйте разные ключи для dev/prod**
2. **Храните секреты в безопасном месте** (1Password, LastPass, etc.)
3. **Ротация ключей** каждые 3-6 месяцев
4. **Ограничьте доступ** к `.env` файлу (chmod 600)
5. **Используйте переменные окружения** на сервере вместо файла `.env`

---

## 📋 Пример полного .env

```bash
# ===================================
# Lead Generation System Configuration
# ===================================

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
API_SECRET_KEY=change-me-in-production

# Redis
REDIS_URL=redis://localhost:6379/0

# Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABC...
TELEGRAM_NOTIFICATION_CHAT_ID=123456789

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Proxy (опционально)
USE_PROXY=false

# CAPTCHA
CAPTCHA_API_KEY=your_2captcha_key
CAPTCHA_ENABLED=true

# Module Settings
MAX_SCRAPING_WORKERS=3
SCRAPING_RATE_LIMIT=1
MIN_QUALIFICATION_SCORE=60
```

---

**Последнее обновление:** 2024-11-17  
**Версия:** 0.1.0

