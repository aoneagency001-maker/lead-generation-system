#!/usr/bin/env python3
"""
🔍 Проверка готовности системы
Проверяет какие credentials заполнены, а что не хватает
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Загружаем .env
load_dotenv()


class SystemReadinessChecker:
    """Проверка готовности системы"""
    
    def __init__(self):
        self.critical_missing = []
        self.important_missing = []
        self.optional_missing = []
        
        self.critical_present = []
        self.important_present = []
        self.optional_present = []
    
    def check_env_var(self, var_name: str, priority: str) -> bool:
        """Проверить наличие переменной окружения"""
        value = os.getenv(var_name)
        is_present = value is not None and value.strip() != ""
        
        if is_present:
            if priority == "critical":
                self.critical_present.append(var_name)
            elif priority == "important":
                self.important_present.append(var_name)
            else:
                self.optional_present.append(var_name)
        else:
            if priority == "critical":
                self.critical_missing.append(var_name)
            elif priority == "important":
                self.important_missing.append(var_name)
            else:
                self.optional_missing.append(var_name)
        
        return is_present
    
    def print_section(self, title: str, icon: str, items: List[str], status_icon: str):
        """Вывести секцию результатов"""
        if items:
            print(f"\n{icon} {title}:")
            for item in items:
                print(f"  {status_icon} {item}")
    
    def check_all(self) -> bool:
        """Проверить все требования"""
        print("=" * 60)
        print("🔍 ПРОВЕРКА ГОТОВНОСТИ СИСТЕМЫ")
        print("=" * 60)
        
        # 🔴 КРИТИЧНОЕ
        print("\n" + "=" * 60)
        print("🔴 КРИТИЧНОЕ (без этого не запустится)")
        print("=" * 60)
        
        critical_checks = [
            ("SUPABASE_URL", "Supabase Database URL"),
            ("SUPABASE_KEY", "Supabase anon key"),
            ("TELEGRAM_BOT_TOKEN", "Telegram Bot Token"),
            ("TELEGRAM_NOTIFICATION_CHAT_ID", "Telegram Chat ID"),
        ]
        
        # Проверяем AI (хотя бы один должен быть)
        has_openai = self.check_env_var("OPENAI_API_KEY", "critical")
        has_gemini = self.check_env_var("GEMINI_API_KEY", "critical")
        has_anthropic = self.check_env_var("ANTHROPIC_API_KEY", "critical")
        
        if not (has_openai or has_gemini or has_anthropic):
            print("  ❌ AI API (нужен хотя бы один: OPENAI_API_KEY / GEMINI_API_KEY / ANTHROPIC_API_KEY)")
            self.critical_missing.append("AI_API_KEY (любой)")
        else:
            ai_providers = []
            if has_openai:
                ai_providers.append("OpenAI")
                # Убираем из missing если добавили
                if "OPENAI_API_KEY" in self.critical_missing:
                    self.critical_missing.remove("OPENAI_API_KEY")
                if "OPENAI_API_KEY" not in self.critical_present:
                    self.critical_present.append("OPENAI_API_KEY")
            if has_gemini:
                ai_providers.append("Gemini")
                if "GEMINI_API_KEY" in self.critical_missing:
                    self.critical_missing.remove("GEMINI_API_KEY")
                if "GEMINI_API_KEY" not in self.critical_present:
                    self.critical_present.append("GEMINI_API_KEY")
            if has_anthropic:
                ai_providers.append("Anthropic")
                if "ANTHROPIC_API_KEY" in self.critical_missing:
                    self.critical_missing.remove("ANTHROPIC_API_KEY")
                if "ANTHROPIC_API_KEY" not in self.critical_present:
                    self.critical_present.append("ANTHROPIC_API_KEY")
            
            print(f"  ✅ AI API ({', '.join(ai_providers)})")
        
        # Проверяем остальные критичные
        for var, description in critical_checks:
            present = self.check_env_var(var, "critical")
            status = "✅" if present else "❌"
            print(f"  {status} {description} ({var})")
        
        # 🟡 ВАЖНОЕ
        print("\n" + "=" * 60)
        print("🟡 ВАЖНОЕ (для полной функциональности)")
        print("=" * 60)
        
        important_checks = [
            ("OLX_EMAIL_1", "OLX Email"),
            ("OLX_PASSWORD_1", "OLX Password"),
            ("OLX_PHONE_1", "OLX Phone"),
            ("PROXY_URL", "Proxy (для масштабирования)"),
            ("CAPTCHA_API_KEY", "2Captcha API Key"),
            ("WHATSAPP_API_URL", "WhatsApp WAHA URL"),
        ]
        
        for var, description in important_checks:
            present = self.check_env_var(var, "important")
            status = "✅" if present else "⚠️"
            print(f"  {status} {description} ({var})")
        
        # 🟢 ОПЦИОНАЛЬНОЕ
        print("\n" + "=" * 60)
        print("🟢 ОПЦИОНАЛЬНОЕ (можно добавить потом)")
        print("=" * 60)
        
        optional_checks = [
            ("KASPI_MERCHANT_ID", "Kaspi Merchant"),
            ("EMAIL_FROM", "Email уведомления"),
            ("TWILIO_ACCOUNT_SID", "Twilio SMS"),
            ("N8N_API_KEY", "n8n Automation"),
            ("GA_TRACKING_ID", "Google Analytics"),
            ("SENTRY_DSN", "Sentry Error Tracking"),
        ]
        
        for var, description in optional_checks:
            present = self.check_env_var(var, "optional")
            status = "✅" if present else "⚪"
            print(f"  {status} {description} ({var})")
        
        # 📊 ИТОГИ
        print("\n" + "=" * 60)
        print("📊 ИТОГИ")
        print("=" * 60)
        
        total_critical = len(self.critical_present) + len(self.critical_missing)
        total_important = len(self.important_present) + len(self.important_missing)
        total_optional = len(self.optional_present) + len(self.optional_missing)
        
        critical_percent = (len(self.critical_present) / total_critical * 100) if total_critical > 0 else 0
        important_percent = (len(self.important_present) / total_important * 100) if total_important > 0 else 0
        optional_percent = (len(self.optional_present) / total_optional * 100) if total_optional > 0 else 0
        
        print(f"\n🔴 Критичное: {len(self.critical_present)}/{total_critical} ({critical_percent:.0f}%)")
        print(f"🟡 Важное: {len(self.important_present)}/{total_important} ({important_percent:.0f}%)")
        print(f"🟢 Опциональное: {len(self.optional_present)}/{total_optional} ({optional_percent:.0f}%)")
        
        # 🎯 СТАТУС
        print("\n" + "=" * 60)
        print("🎯 СТАТУС СИСТЕМЫ")
        print("=" * 60)
        
        if len(self.critical_missing) == 0:
            print("\n✅ СИСТЕМА ГОТОВА К ЗАПУСКУ!")
            print("   Все критичные требования выполнены.")
            
            if len(self.important_missing) > 0:
                print(f"\n⚠️  Рекомендуется добавить важные параметры ({len(self.important_missing)} шт):")
                for item in self.important_missing:
                    print(f"   - {item}")
            
            return True
        else:
            print("\n❌ СИСТЕМА НЕ ГОТОВА")
            print(f"   Не хватает {len(self.critical_missing)} критичных параметров:")
            for item in self.critical_missing:
                print(f"   - {item}")
            
            print("\n💡 ЧТО ДЕЛАТЬ:")
            print("   1. Открой: MD/v0.3/20.11.2025_00:50_БЫСТРЫЙ_СТАРТ_ЧТО_НУЖНО.md")
            print("   2. Следуй инструкциям для получения недостающих параметров")
            print("   3. Добавь их в .env файл")
            print("   4. Запусти эту проверку снова")
            
            return False
    
    def check_playwright(self) -> bool:
        """Проверить установлен ли Playwright"""
        print("\n" + "=" * 60)
        print("🎭 ПРОВЕРКА PLAYWRIGHT")
        print("=" * 60)
        
        try:
            from playwright.sync_api import sync_playwright
            print("  ✅ Playwright установлен")
            
            # Проверяем браузеры
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    browser.close()
                    print("  ✅ Chromium browser установлен")
                    return True
            except Exception as e:
                print(f"  ❌ Chromium browser не установлен: {e}")
                print("\n💡 Установи командой: playwright install chromium")
                return False
        except ImportError:
            print("  ❌ Playwright не установлен")
            print("\n💡 Установи командой: pip install playwright")
            return False
    
    def check_database_connection(self) -> bool:
        """Проверить подключение к Supabase"""
        print("\n" + "=" * 60)
        print("🗄️  ПРОВЕРКА БАЗЫ ДАННЫХ")
        print("=" * 60)
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            print("  ⚠️  SUPABASE_URL или SUPABASE_KEY не настроены")
            return False
        
        try:
            from core.database.supabase_client import get_supabase_client
            client = get_supabase_client()
            
            # Пробуем простой запрос
            response = client.table("niches").select("id").limit(1).execute()
            print("  ✅ Подключение к Supabase работает")
            return True
        except Exception as e:
            print(f"  ❌ Ошибка подключения к Supabase: {e}")
            print("\n💡 Проверь:")
            print("   1. Правильность SUPABASE_URL и SUPABASE_KEY")
            print("   2. Применены ли схемы БД: python scripts/setup_database.py")
            return False
    
    def check_telegram_bot(self) -> bool:
        """Проверить Telegram бота"""
        print("\n" + "=" * 60)
        print("🤖 ПРОВЕРКА TELEGRAM БОТА")
        print("=" * 60)
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        if not bot_token:
            print("  ⚠️  TELEGRAM_BOT_TOKEN не настроен")
            return False
        
        try:
            import requests
            response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                bot_name = data.get("result", {}).get("username", "Unknown")
                print(f"  ✅ Telegram бот работает: @{bot_name}")
                return True
            else:
                print(f"  ❌ Ошибка Telegram API: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ Не удалось проверить Telegram бота: {e}")
            return False


def main():
    """Главная функция"""
    checker = SystemReadinessChecker()
    
    # Основная проверка
    system_ready = checker.check_all()
    
    # Дополнительные проверки
    playwright_ok = checker.check_playwright()
    
    if system_ready:
        db_ok = checker.check_database_connection()
        telegram_ok = checker.check_telegram_bot()
    
    # Финальный статус
    print("\n" + "=" * 60)
    print("🏁 ФИНАЛЬНЫЙ СТАТУС")
    print("=" * 60)
    
    if system_ready:
        print("\n🎉 ВСЁ ГОТОВО! Можешь запускать систему:")
        print("\n   uvicorn core.api.main:app --reload")
        print("\n   Затем открой: http://localhost:8000/health")
    else:
        print("\n⏳ СИСТЕМА НЕ ГОТОВА")
        print("\n📖 Смотри инструкции:")
        print("   MD/v0.3/20.11.2025_00:50_БЫСТРЫЙ_СТАРТ_ЧТО_НУЖНО.md")
    
    print("\n" + "=" * 60)
    
    return 0 if system_ready else 1


if __name__ == "__main__":
    sys.exit(main())

