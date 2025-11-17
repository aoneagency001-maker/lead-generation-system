#!/bin/bash
# Скрипт для перезапуска Lead Generation System

cd "$(dirname "$0")/.." || exit

echo "🛑 Останавливаю сервер..."
if [ -f uvicorn.pid ]; then
    kill $(cat uvicorn.pid) 2>/dev/null
    rm uvicorn.pid
    sleep 2
fi

echo "🧹 Очищаю кэш..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

echo "🚀 Запускаю сервер..."
source venv/bin/activate
nohup uvicorn core.api.main:app --reload --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
echo $! > uvicorn.pid

sleep 3

echo "✅ Сервер перезапущен (PID: $(cat uvicorn.pid))"
echo "📊 Проверка: http://localhost:8000/api/health"
curl -s http://localhost:8000/api/health | python3 -m json.tool

