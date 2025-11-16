# Модуль 5: Analytics (Аналитика)

Дашборды и метрики для отслеживания эффективности всей системы.

## Функции

- **Metabase дашборды**: Красивые графики и таблицы
- **Ключевые метрики**: CPL, ROI, конверсии
- **Воронка продаж**: TOFU → MOFU → BOFU
- **Сравнение ниш**: Какие ниши работают лучше
- **Реалтайм**: Обновление данных каждые 5 минут

## Установка

```bash
# Запустите Metabase
docker-compose up -d metabase

# Откройте UI
open http://localhost:3000
```

## Настройка Metabase

1. Откройте http://localhost:3000
2. Создайте аккаунт администратора
3. Подключите Supabase:
   - Тип: PostgreSQL
   - Host: ваш Supabase host
   - База: postgres
   - User/Password из Supabase

## Основные метрики

### 1. CPL (Cost Per Lead)

```sql
SELECT 
  n.name as niche,
  SUM(c.spent) / COUNT(l.id) as cpl
FROM campaigns c
JOIN niches n ON c.niche_id = n.id
LEFT JOIN ads a ON a.campaign_id = c.id
LEFT JOIN leads l ON l.ad_id = a.id
GROUP BY n.name
```

### 2. ROI по нишам

```sql
SELECT 
  n.name,
  (SUM(closed_deals * avg_price) - SUM(c.spent)) / SUM(c.spent) * 100 as roi
FROM niches n
JOIN campaigns c ON c.niche_id = n.id
GROUP BY n.name
```

### 3. Воронка конверсии

```sql
SELECT 
  status,
  COUNT(*) as count
FROM leads
GROUP BY status
ORDER BY 
  CASE status
    WHEN 'new' THEN 1
    WHEN 'contacted' THEN 2
    WHEN 'qualified' THEN 3
    WHEN 'hot' THEN 4
    WHEN 'won' THEN 5
  END
```

## Программное использование

```python
from modules.analytics.metrics.cpl_calculator import calculate_cpl

cpl = calculate_cpl(campaign_id="xxx")
print(f"CPL: {cpl} тенге")

if cpl > 500:
    print("⚠️ CPL слишком высокий! Нужно оптимизировать кампанию")
```

## Дашборды

### 1. Главный дашборд
- Общее количество лидов
- CPL по всем кампаниям
- ROI
- График лидов за последние 30 дней

### 2. Дашборд ниш
- Сравнение ниш по метрикам
- Какие ниши приносят больше прибыли
- Рекомендации по масштабированию

### 3. Дашборд кампаний
- Статус активных кампаний
- Бюджет vs Spent
- Количество объявлений и лидов

## TODO

- [ ] Прогнозирование CPL с помощью ML
- [ ] Alerts при аномалиях (резкий рост CPL)
- [ ] Экспорт отчетов в PDF
- [ ] Автоматические еженедельные отчеты на email

