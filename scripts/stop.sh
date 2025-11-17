#!/bin/bash
# Скрипт для остановки Lead Generation System

cd "$(dirname "$0")/.." || exit

if [ -f uvicorn.pid ]; then
    PID=$(cat uvicorn.pid)
    echo "🛑 Останавливаю сервер (PID: $PID)..."
    kill $PID 2>/dev/null
    rm uvicorn.pid
    echo "✅ Сервер остановлен"
else
    echo "⚠️  PID файл не найден. Ищу процессы вручную..."
    pkill -f "uvicorn core.api.main:app"
    echo "✅ Все процессы остановлены"
fi

