# ✅ Проверка конфигурации

**Дата:** 21.11.2025 05:33

---

## ✅ Проверка workflow файла

### Workflow файл: `.github/workflows/deploy.yml`

✅ **Синтаксис YAML:** Корректен  
✅ **Используемые secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

✅ **Триггеры:**
- Push в `main` (только для `telegram-notifications-service/`)
- Ручной запуск (workflow_dispatch)

✅ **Репозиторий:** `aoneagency001-maker/lead-generation-system`

---

## 🔍 Способы проверки GitHub Secrets

### Способ 1: Через GitHub UI (самый простой)

1. Откройте: https://github.com/aoneagency001-maker/lead-generation-system/settings/secrets/actions
2. Проверьте наличие секретов:
   - ✅ `AWS_ACCESS_KEY_ID`
   - ✅ `AWS_SECRET_ACCESS_KEY`

**Если оба секрета видны** → ✅ Всё настроено правильно!

---

### Способ 2: Тестовый запуск workflow (рекомендуется)

1. Откройте: https://github.com/aoneagency001-maker/lead-generation-system/actions
2. Выберите workflow **"🚀 Deploy to AWS Lambda"**
3. Нажмите **"Run workflow"** (справа)
4. Выберите:
   - Branch: `main`
   - Stage: `dev`
5. Нажмите **"Run workflow"**

**Что произойдёт:**

✅ **Если secrets настроены:**
- Workflow начнёт выполняться
- Вы увидите логи сборки и деплоя
- В конце будет summary с endpoint URL

❌ **Если secrets НЕ настроены:**
- Workflow упадёт с ошибкой на шаге "Configure AWS credentials"
- Ошибка: `AWS_ACCESS_KEY_ID not found` или `AWS_SECRET_ACCESS_KEY not found`

---

### Способ 3: Через скрипт (требует GitHub Token)

```bash
cd telegram-notifications-service

# Установите GitHub Token
export GITHUB_TOKEN=your_github_personal_access_token

# Запустите проверку
./scripts/check-github-secrets.sh
```

**Как получить GitHub Token:**
1. Откройте: https://github.com/settings/tokens
2. Нажмите "Generate new token (classic)"
3. Выберите права: `repo` (для private) или `public_repo` (для public)
4. Скопируйте токен

---

## 📋 Чеклист проверки

- [ ] Открыл GitHub Settings → Secrets → Actions
- [ ] Вижу `AWS_ACCESS_KEY_ID` в списке
- [ ] Вижу `AWS_SECRET_ACCESS_KEY` в списке
- [ ] Запустил тестовый workflow
- [ ] Workflow выполнился успешно (или увидел конкретную ошибку)

---

## 🎯 Быстрая проверка

**Самый быстрый способ:**

1. Откройте: https://github.com/aoneagency001-maker/lead-generation-system/actions/workflows/deploy.yml
2. Нажмите "Run workflow"
3. Выберите stage: `dev`
4. Нажмите "Run workflow"

**Если workflow запустился** → ✅ Secrets настроены!  
**Если ошибка** → ❌ Нужно добавить secrets

---

## 📝 Требуемые значения secrets

Если нужно добавить или проверить значения:

### AWS_ACCESS_KEY_ID
```
⚠️ Установите значение из AWS Console
```

### AWS_SECRET_ACCESS_KEY
```
⚠️ Установите значение из AWS Console
```

**⚠️ ВАЖНО:** 
- Никогда не коммитьте реальные значения секретов в Git!
- Значения должны быть точными, без лишних пробелов
- Используйте GitHub Secrets для хранения

---

## ✅ Итог

**Workflow файл:** ✅ Корректен  
**Конфигурация:** ✅ Правильная  
**Secrets:** ⏳ Требует проверки (через GitHub UI или тестовый запуск)

**Следующий шаг:** Запустите тестовый workflow для финальной проверки!

---

## 🔗 Полезные ссылки

- **GitHub Secrets:** https://github.com/aoneagency001-maker/lead-generation-system/settings/secrets/actions
- **GitHub Actions:** https://github.com/aoneagency001-maker/lead-generation-system/actions
- **Workflow файл:** `.github/workflows/deploy.yml`
- **Документация:** `CI_CD_README.md`

