#!/bin/bash

echo "🔍 Проверка сервера на порту 8001..."

# Проверка процесса
if pgrep -f "uvicorn.*8001" > /dev/null; then
    echo "✅ Сервер запущен (процесс найден)"
else
    echo "❌ Сервер НЕ запущен"
    exit 1
fi

# Проверка порта
if lsof -i :8001 > /dev/null 2>&1; then
    echo "✅ Порт 8001 занят"
else
    echo "❌ Порт 8001 свободен"
    exit 1
fi

# Проверка health endpoint
echo ""
echo "📡 Проверка http://localhost:8001/api/health..."
response=$(curl -s -w "\n%{http_code}" http://localhost:8001/api/health 2>&1)
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    echo "✅ Health endpoint работает (HTTP $http_code)"
    echo "   Ответ: $body"
else
    echo "❌ Health endpoint не работает (HTTP $http_code)"
    echo "   Ответ: $body"
fi

# Проверка метрики endpoint
echo ""
echo "📡 Проверка http://localhost:8001/api/yandex-metrika/counters..."
response=$(curl -s -w "\n%{http_code}" http://localhost:8001/api/yandex-metrika/counters 2>&1)
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    echo "✅ Метрика endpoint работает (HTTP $http_code)"
    counters_count=$(echo "$body" | grep -o '"id"' | wc -l | tr -d ' ')
    echo "   Найдено счетчиков: $counters_count"
elif [ "$http_code" = "401" ]; then
    echo "⚠️  Метрика endpoint требует авторизацию (HTTP $http_code)"
    echo "   Проверьте токен в .env"
else
    echo "❌ Метрика endpoint не работает (HTTP $http_code)"
    echo "   Ответ: $body"
fi

echo ""
echo "🌐 Сервер доступен по адресам:"
echo "   - http://localhost:8001"
echo "   - http://127.0.0.1:8001"
echo ""
echo "📚 Документация API:"
echo "   - http://localhost:8001/docs"
echo "   - http://localhost:8001/redoc"
echo ""
echo "✅ Все готово! Откройте в браузере:"
echo "   http://localhost:8001/api/yandex-metrika/counters"

