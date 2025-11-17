#!/bin/bash

echo "🚀 Lead Generation System - Загрузка на GitHub"
echo "=============================================="
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Шаг 1: Откройте в браузере:${NC}"
echo "https://github.com/new"
echo ""

echo -e "${YELLOW}Шаг 2: Заполните форму:${NC}"
echo "Repository name: lead-generation-system"
echo "Description: Модульная система автоматизации лид-генерации для Казахстана (OLX, Kaspi)"
echo "Visibility: Public (или Private)"
echo "⚠️  НЕ добавляйте README, .gitignore, license"
echo ""

read -p "Нажмите Enter после создания репозитория..."
echo ""

echo -e "${YELLOW}Шаг 3: Введите ваш GitHub username:${NC}"
read -p "Username: " USERNAME

if [ -z "$USERNAME" ]; then
    echo "❌ Username не может быть пустым!"
    exit 1
fi

echo ""
echo -e "${BLUE}Добавляю remote...${NC}"
git remote add origin https://github.com/$USERNAME/lead-generation-system.git

echo -e "${BLUE}Проверяю ветку...${NC}"
git branch -M main

echo -e "${BLUE}Загружаю код...${NC}"
git push -u origin main

echo -e "${BLUE}Загружаю тег v0.0-demo...${NC}"
git push origin v0.0-demo

echo ""
echo -e "${GREEN}✅ Успешно загружено!${NC}"
echo ""
echo "🌐 Ваш репозиторий:"
echo "https://github.com/$USERNAME/lead-generation-system"
echo ""
echo "📝 Следующие шаги:"
echo "1. Создайте Release из тега v0.0-demo"
echo "2. Добавьте Topics: lead-generation, kazakhstan, olx, kaspi, fastapi"
echo "3. Прочитайте QUICKSTART.md для начала работы"
echo ""
