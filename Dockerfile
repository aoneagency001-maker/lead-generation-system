FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Установка Playwright браузеров
RUN playwright install chromium && \
    playwright install-deps chromium

# Копирование кода приложения
COPY . .

# Создание директорий для логов и данных
RUN mkdir -p /app/logs /app/data

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose порт
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Запуск приложения
CMD ["uvicorn", "core.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

