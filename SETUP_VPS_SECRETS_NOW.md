# ⚡ НАСТРОЙКА СЕКРЕТОВ ПРЯМО СЕЙЧАС

**Дата:** 23.11.2025 04:15  
**Статус:** ✅ SSH ключ готов, нужно добавить секреты

---

## ✅ Что уже готово

- ✅ SSH ключ сгенерирован: `~/.ssh/github_actions_deploy`
- ✅ GitHub CLI авторизован
- ✅ Публичный ключ готов для VPS
- ✅ Приватный ключ готов для GitHub Secrets

---

## 🚀 3 команды для добавления секретов

**Замени `<VPS_IP>` и `<USER>` на свои значения:**

```bash
# 1. Добавить VPS_HOST (замени <VPS_IP>)
echo "<VPS_IP>" | gh secret set VPS_HOST --repo aoneagency001-maker/lead-generation-system

# 2. Добавить VPS_USER (замени <USER> на root или ubuntu)
echo "<USER>" | gh secret set VPS_USER --repo aoneagency001-maker/lead-generation-system

# 3. Добавить VPS_SSH_KEY (приватный ключ)
cat ~/.ssh/github_actions_deploy | gh secret set VPS_SSH_KEY --repo aoneagency001-maker/lead-generation-system
```

**Пример (если VPS IP = 123.45.67.89, пользователь = root):**
```bash
echo "123.45.67.89" | gh secret set VPS_HOST --repo aoneagency001-maker/lead-generation-system
echo "root" | gh secret set VPS_USER --repo aoneagency001-maker/lead-generation-system
cat ~/.ssh/github_actions_deploy | gh secret set VPS_SSH_KEY --repo aoneagency001-maker/lead-generation-system
```

---

## 📤 Добавить публичный ключ на VPS

**Публичный ключ:**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMwT/Dn9wnIj/zQFK2rkK0vpCBIu0Ke/yxkmXZFNSeDS github-actions-deploy
```

**Команда (замени `<VPS_IP>` и `<USER>`):**
```bash
ssh-copy-id -i ~/.ssh/github_actions_deploy.pub <USER>@<VPS_IP>
```

**Или вручную на VPS:**
```bash
# Подключись к VPS
ssh <USER>@<VPS_IP>

# На VPS выполни:
mkdir -p ~/.ssh
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMwT/Dn9wnIj/zQFK2rkK0vpCBIu0Ke/yxkmXZFNSeDS github-actions-deploy" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
exit
```

---

## ✅ Проверка

```bash
# Проверить что секреты добавлены
./scripts/check_github_secrets.sh

# Проверить SSH подключение
ssh -i ~/.ssh/github_actions_deploy <USER>@<VPS_IP>
```

---

## 🧪 Тест workflow

1. Открой: https://github.com/aoneagency001-maker/lead-generation-system/actions
2. Выбери "🚀 Auto Deploy to VPS"
3. Нажми "Run workflow" → "Run workflow"

---

**Готово!** После этого всё должно работать.

