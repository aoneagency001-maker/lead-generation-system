# ⚡ Быстрые команды

## Управление сервером

```bash
# Перейти в директорию проекта
cd /Users/vbut/lead-generation-system

# Остановить сервер
./scripts/stop.sh

# Перезапустить сервер
./scripts/restart.sh

# Просмотр логов (live)
tail -f uvicorn.log

# Просмотр последних 50 строк логов
tail -50 uvicorn.log

# Проверка статуса
curl http://localhost:8000/api/health | python3 -m json.tool
```

## API Тестирование

```bash
# Health check
curl http://localhost:8000/api/health

# Открыть Swagger UI в браузере
open http://localhost:8000/docs

# Получить список ниш
curl http://localhost:8000/api/niches

# Получить список кампаний
curl http://localhost:8000/api/campaigns

# Получить список лидов
curl http://localhost:8000/api/leads
```

## Разработка

```bash
# Активировать venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Применить схему БД
python scripts/setup_database.py

# Тесты подключения
python scripts/test_connection.py

# Очистить кэш
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
```

## Полезные ссылки

- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health:** http://localhost:8000/api/health
- **OpenAPI JSON:** http://localhost:8000/openapi.json

## Отладка

```bash
# Проверить запущен ли сервер
lsof -i :8000

# Убить процесс на порту 8000
lsof -ti :8000 | xargs kill -9

# Проверить PID
cat uvicorn.pid

# Проверить процессы Python
ps aux | grep python
```

