#!/usr/bin/env python3
"""
Скрипт для регистрации custom events в GA4
на основе гайда GA4_Custom_Events_Full_Guide.md

В GA4 события регистрируются автоматически при первой отправке.
Этот скрипт отправляет тестовые события через Measurement Protocol,
чтобы они зарегистрировались в GA4 Property.

Требования:
- GA4 Measurement ID (G-XXXXXXXXXX)
- GA4 API Secret (создается в Admin → Data Streams → Measurement Protocol API secrets)
- Или Service Account для получения Measurement ID из Property

Примечание:
- События появятся в GA4 через несколько минут после отправки
- Можно проверить в Real-time отчете GA4
"""

import os
import sys
import logging
import json
import time
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from collections import deque

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import httpx
except ImportError:
    print("❌ Требуется пакет httpx. Установите: pip install httpx")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GA4EventCreator:
    """Класс для регистрации custom events в GA4 через Measurement Protocol"""
    
    def __init__(
        self,
        measurement_id: Optional[str] = None,
        api_secret: Optional[str] = None,
        credentials_path: Optional[str] = None,
        property_id: Optional[str] = None
    ):
        """
        Инициализация клиента для отправки событий в GA4
        
        Args:
            measurement_id: GA4 Measurement ID (G-XXXXXXXXXX)
            api_secret: GA4 API Secret (из Measurement Protocol API secrets)
            credentials_path: Путь к Service Account JSON (для получения Measurement ID)
            property_id: Property ID (для получения Measurement ID через Admin API)
        """
        # Measurement ID и API Secret
        self.measurement_id = measurement_id or os.getenv("GA4_MEASUREMENT_ID")
        self.api_secret = api_secret or os.getenv("GA4_API_SECRET")
        
        # Если нет Measurement ID, пытаемся получить через Admin API
        if not self.measurement_id:
            self.measurement_id = self._get_measurement_id_from_property(
                credentials_path, property_id
            )
        
        if not self.measurement_id:
            raise ValueError(
                "GA4_MEASUREMENT_ID не установлен. "
                "Установите в .env или передайте как параметр. "
                "Формат: G-XXXXXXXXXX"
            )
        
        if not self.api_secret:
            raise ValueError(
                "GA4_API_SECRET не установлен. "
                "Создайте в GA4: Admin → Data Streams → Measurement Protocol API secrets"
            )
        
        # URL для Measurement Protocol
        self.endpoint = f"https://www.google-analytics.com/mp/collect"
        
        # Rate limiting: max 5-8 requests/sec (safe zone, не 10!)
        self.max_requests_per_second = 5
        self.min_delay_between_requests = 1.0 / self.max_requests_per_second  # ~0.2 сек
        
        # Queue для событий
        self.event_queue = deque()
        self.processing = False
        
        logger.info(f"✅ GA4 Event Creator инициализирован")
        logger.info(f"   Measurement ID: {self.measurement_id}")
        logger.info(f"   API Secret: {'*' * (len(self.api_secret) - 4) + self.api_secret[-4:]}")
        logger.info(f"   Rate limit: {self.max_requests_per_second} req/sec (safe zone)")
    
    def _get_measurement_id_from_property(
        self,
        credentials_path: Optional[str],
        property_id: Optional[str]
    ) -> Optional[str]:
        """Пытается получить Measurement ID через Admin API"""
        try:
            from library.integrations.google_analytics import GoogleAnalyticsClient
            
            prop_id = property_id or os.getenv("GOOGLE_ANALYTICS_PROPERTY_ID")
            if not prop_id:
                return None
            
            creds_path = (
                credentials_path 
                or os.getenv("GOOGLE_ANALYTICS_CREDENTIALS_PATH")
                or "credentials/ga4-service-account.json"
            )
            
            if not os.path.exists(creds_path):
                return None
            
            # Создаем клиент для получения информации о Property
            client = GoogleAnalyticsClient(
                credentials_path=creds_path,
                property_id=prop_id
            )
            
            # Получаем информацию о Property
            # Примечание: Measurement ID обычно начинается с G- и связан с Data Stream
            # Для упрощения, возвращаем None и просим указать вручную
            logger.warning("⚠️  Не удалось автоматически получить Measurement ID")
            logger.info("💡 Укажите GA4_MEASUREMENT_ID в .env (формат: G-XXXXXXXXXX)")
            return None
            
        except Exception as e:
            logger.warning(f"⚠️  Не удалось получить Measurement ID: {e}")
            return None
    
    def get_custom_events_list(self) -> List[Dict[str, Any]]:
        """
        Возвращает список всех custom events из гайда
        
        Returns:
            Список словарей с информацией о событиях
        """
        events = [
            # Tier 1: CRITICAL - Conversion Events
            {
                "event_name": "form_submit",
                "description": "Форма успешно отправлена",
                "tier": "Tier 1: CRITICAL",
                "category": "Conversion",
                "parameters": ["form_id", "form_name", "form_fields", "submission_time_seconds", "email"]
            },
            {
                "event_name": "lead_qualified",
                "description": "Лид прошёл валидацию",
                "tier": "Tier 1: CRITICAL",
                "category": "Conversion",
                "parameters": ["hot_score", "segment", "intent_score", "quality_index", "revenue_potential"]
            },
            {
                "event_name": "booking_confirmed",
                "description": "Бронь подтверждена",
                "tier": "Tier 1: CRITICAL",
                "category": "Conversion",
                "parameters": ["booking_id", "booking_type", "revenue", "currency"]
            },
            {
                "event_name": "contact_created",
                "description": "Контакт создан в CRM",
                "tier": "Tier 1: CRITICAL",
                "category": "Conversion",
                "parameters": ["contact_id", "contact_source", "contact_type"]
            },
            
            # Tier 1: CRITICAL - Engagement Events
            {
                "event_name": "form_field_focus",
                "description": "Фокус на поле формы",
                "tier": "Tier 1: CRITICAL",
                "category": "Engagement",
                "parameters": ["form_id", "field_name", "field_type"]
            },
            {
                "event_name": "form_field_fill",
                "description": "Заполнение поля формы",
                "tier": "Tier 1: CRITICAL",
                "category": "Engagement",
                "parameters": ["form_id", "field_name", "field_type", "fill_time_seconds"]
            },
            {
                "event_name": "form_error",
                "description": "Ошибка валидации формы",
                "tier": "Tier 1: CRITICAL",
                "category": "Engagement",
                "parameters": ["form_id", "field_name", "error_msg", "error_type"]
            },
            {
                "event_name": "phone_view",
                "description": "Просмотр номера телефона",
                "tier": "Tier 1: CRITICAL",
                "category": "Engagement",
                "parameters": ["phone_number", "location", "page_url"]
            },
            {
                "event_name": "email_copy",
                "description": "Копирование email",
                "tier": "Tier 1: CRITICAL",
                "category": "Engagement",
                "parameters": ["email", "page_url", "copy_method"]
            },
            {
                "event_name": "cta_click",
                "description": "Клик на CTA кнопку",
                "tier": "Tier 1: CRITICAL",
                "category": "Engagement",
                "parameters": ["cta_text", "cta_position", "cta_type", "page_url"]
            },
            
            # Tier 1: CRITICAL - Quality Events
            {
                "event_name": "time_on_page",
                "description": "Время на странице (каждые 10 сек)",
                "tier": "Tier 1: CRITICAL",
                "category": "Quality",
                "parameters": ["time_spent", "page_url", "page_title"]
            },
            {
                "event_name": "scroll_depth",
                "description": "Глубина скролла (25%, 50%, 75%, 100%)",
                "tier": "Tier 1: CRITICAL",
                "category": "Quality",
                "parameters": ["scroll_percent", "page_url", "time_to_scroll"]
            },
            {
                "event_name": "video_play",
                "description": "Воспроизведение видео",
                "tier": "Tier 1: CRITICAL",
                "category": "Quality",
                "parameters": ["video_id", "video_title", "video_duration", "play_time", "completion_percent"]
            },
            {
                "event_name": "document_download",
                "description": "Скачивание документа",
                "tier": "Tier 1: CRITICAL",
                "category": "Quality",
                "parameters": ["document_name", "document_type", "document_category", "file_size_kb"]
            },
            {
                "event_name": "content_view",
                "description": "Просмотр контента",
                "tier": "Tier 1: CRITICAL",
                "category": "Quality",
                "parameters": ["content_type", "content_id", "content_title", "view_duration"]
            },
            
            # Tier 2: IMPORTANT - Lead Source Events
            {
                "event_name": "utm_source_track",
                "description": "Отслеживание источника трафика",
                "tier": "Tier 2: IMPORTANT",
                "category": "Lead Source",
                "parameters": ["utm_source", "utm_medium", "utm_campaign"]
            },
            {
                "event_name": "utm_medium_track",
                "description": "Отслеживание канала трафика",
                "tier": "Tier 2: IMPORTANT",
                "category": "Lead Source",
                "parameters": ["utm_medium", "utm_source", "traffic_type"]
            },
            {
                "event_name": "utm_campaign_track",
                "description": "Отслеживание кампании",
                "tier": "Tier 2: IMPORTANT",
                "category": "Lead Source",
                "parameters": ["utm_campaign", "campaign_id", "campaign_name"]
            },
            {
                "event_name": "referrer_track",
                "description": "Отслеживание реферера",
                "tier": "Tier 2: IMPORTANT",
                "category": "Lead Source",
                "parameters": ["referrer_url", "referrer_domain", "referrer_type"]
            },
            
            # Tier 2: IMPORTANT - Segment Events
            {
                "event_name": "device_info",
                "description": "Информация об устройстве",
                "tier": "Tier 2: IMPORTANT",
                "category": "Segment",
                "parameters": ["device_type", "device_brand", "device_model"]
            },
            {
                "event_name": "browser_type",
                "description": "Тип браузера",
                "tier": "Tier 2: IMPORTANT",
                "category": "Segment",
                "parameters": ["browser_name", "browser_version"]
            },
            {
                "event_name": "os_type",
                "description": "Тип операционной системы",
                "tier": "Tier 2: IMPORTANT",
                "category": "Segment",
                "parameters": ["os_name", "os_version"]
            },
            {
                "event_name": "location_detect",
                "description": "Геолокация пользователя",
                "tier": "Tier 2: IMPORTANT",
                "category": "Segment",
                "parameters": ["country", "city", "region", "timezone"]
            },
            {
                "event_name": "language_detect",
                "description": "Язык браузера",
                "tier": "Tier 2: IMPORTANT",
                "category": "Segment",
                "parameters": ["language", "locale"]
            },
            
            # Tier 2: IMPORTANT - Intent Signals
            {
                "event_name": "search_query",
                "description": "Поиск на сайте",
                "tier": "Tier 2: IMPORTANT",
                "category": "Intent",
                "parameters": ["query", "results_count", "search_type"]
            },
            {
                "event_name": "product_view",
                "description": "Просмотр товара",
                "tier": "Tier 2: IMPORTANT",
                "category": "Intent",
                "parameters": ["product_id", "product_name", "product_category", "product_price"]
            },
            {
                "event_name": "comparison_view",
                "description": "Сравнение товаров",
                "tier": "Tier 2: IMPORTANT",
                "category": "Intent",
                "parameters": ["products_count", "comparison_type"]
            },
            {
                "event_name": "wishlist_add",
                "description": "Добавление в wishlist",
                "tier": "Tier 2: IMPORTANT",
                "category": "Intent",
                "parameters": ["product_id", "product_name"]
            },
            {
                "event_name": "cart_activity",
                "description": "Активность в корзине",
                "tier": "Tier 2: IMPORTANT",
                "category": "Intent",
                "parameters": ["action_type", "items_count", "cart_value"]
            },
            
            # Tier 3: NICE-TO-HAVE - Retention Events
            {
                "event_name": "repeat_visit",
                "description": "Повторный визит",
                "tier": "Tier 3: NICE-TO-HAVE",
                "category": "Retention",
                "parameters": ["visit_number", "days_since_first", "last_visit_date"]
            },
            {
                "event_name": "days_since_first",
                "description": "Дни с первого визита",
                "tier": "Tier 3: NICE-TO-HAVE",
                "category": "Retention",
                "parameters": ["days_count", "first_visit_date"]
            },
            {
                "event_name": "session_count",
                "description": "Номер сессии",
                "tier": "Tier 3: NICE-TO-HAVE",
                "category": "Retention",
                "parameters": ["session_number", "total_sessions"]
            },
            {
                "event_name": "return_time",
                "description": "Время между визитами",
                "tier": "Tier 3: NICE-TO-HAVE",
                "category": "Retention",
                "parameters": ["hours_since_last", "days_since_last"]
            },
            
            # Tier 3: NICE-TO-HAVE - Micro-Conversions
            {
                "event_name": "newsletter_signup",
                "description": "Подписка на рассылку",
                "tier": "Tier 3: NICE-TO-HAVE",
                "category": "Micro-Conversion",
                "parameters": ["email", "signup_source", "signup_type"]
            },
            {
                "event_name": "demo_request",
                "description": "Запрос демо",
                "tier": "Tier 3: NICE-TO-HAVE",
                "category": "Micro-Conversion",
                "parameters": ["demo_type", "request_source"]
            },
            {
                "event_name": "webinar_register",
                "description": "Регистрация на вебинар",
                "tier": "Tier 3: NICE-TO-HAVE",
                "category": "Micro-Conversion",
                "parameters": ["webinar_id", "webinar_name", "webinar_date"]
            },
            {
                "event_name": "ebook_download",
                "description": "Скачивание ebook",
                "tier": "Tier 3: NICE-TO-HAVE",
                "category": "Micro-Conversion",
                "parameters": ["ebook_name", "ebook_type", "file_size_kb"]
            },
            {
                "event_name": "coupon_apply",
                "description": "Применение купона",
                "tier": "Tier 3: NICE-TO-HAVE",
                "category": "Micro-Conversion",
                "parameters": ["coupon_code", "discount_amount", "discount_percent"]
            },
            
            # Telegram Bot Events
            {
                "event_name": "telegram_message",
                "description": "Сообщение в Telegram боте",
                "tier": "Tier 1: CRITICAL",
                "category": "Bot",
                "parameters": ["message_type", "message_length", "response_time_seconds", "bot_message_count"]
            },
            {
                "event_name": "user_intent_detected",
                "description": "Обнаружен intent пользователя",
                "tier": "Tier 1: CRITICAL",
                "category": "Bot",
                "parameters": ["intent", "confidence", "intent_type"]
            },
            {
                "event_name": "contact_shared",
                "description": "Контакт поделен в Telegram",
                "tier": "Tier 1: CRITICAL",
                "category": "Bot",
                "parameters": ["phone", "first_name", "last_name", "source"]
            },
        ]
        
        return events
    
    def _validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация и ограничение параметров согласно GA4 limits
        
        Args:
            parameters: Исходные параметры
        
        Returns:
            Валидированные параметры (max 20, не больше 25)
        """
        if not parameters:
            return {}
        
        # Ограничиваем до 20 параметров (best practice, не 25!)
        validated = {}
        param_count = 0
        max_params = 20
        
        for key, value in parameters.items():
            if param_count >= max_params:
                logger.warning(f"⚠️  Превышен лимит параметров ({max_params}), остальные пропущены")
                break
            
            # Проверка на PII (Personally Identifiable Information)
            key_lower = key.lower()
            value_str = str(value).lower()
            
            # Проверяем, не является ли параметр PII
            pii_keywords = ['email', 'phone', 'name', 'user_id', 'password', 'credit_card']
            if any(pii in key_lower for pii in pii_keywords):
                # Если это PII, хешируем или пропускаем
                if '@' in value_str or '+' in value_str or len(value_str) > 50:
                    logger.warning(f"⚠️  Пропущен PII параметр: {key}")
                    continue
            
            # Ограничиваем длину имени параметра (40 символов)
            if len(key) > 40:
                key = key[:40]
                logger.warning(f"⚠️  Имя параметра обрезано до 40 символов: {key}")
            
            # Ограничиваем длину значения (100 символов)
            if isinstance(value, str) and len(value) > 100:
                value = value[:100]
                logger.warning(f"⚠️  Значение параметра обрезано до 100 символов: {key}")
            
            validated[key] = value
            param_count += 1
        
        return validated
    
    def send_event(
        self,
        event_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        client_id: Optional[str] = None,
        max_retries: int = 3
    ) -> bool:
        """
        Отправляет событие в GA4 через Measurement Protocol с exponential backoff
        
        Args:
            event_name: Название события (max 40 символов)
            parameters: Параметры события (max 20, валидируются)
            client_id: Client ID (по умолчанию генерируется)
            max_retries: Максимальное количество попыток
        
        Returns:
            True если событие отправлено успешно
        """
        # Валидация имени события (max 40 символов)
        if len(event_name) > 40:
            logger.error(f"❌ Имя события слишком длинное ({len(event_name)} > 40): {event_name}")
            return False
        
        # Валидация параметров
        validated_params = self._validate_parameters(parameters or {})
        
        if not client_id:
            # Генерируем уникальный client_id для тестового события
            client_id = str(uuid.uuid4())
        
        payload = {
            "client_id": client_id,
            "events": [
                {
                    "name": event_name,
                    "params": validated_params
                }
            ]
        }
        
        url = f"{self.endpoint}?measurement_id={self.measurement_id}&api_secret={self.api_secret}"
        
        # Exponential backoff retry logic
        for attempt in range(max_retries):
            try:
                response = httpx.post(url, json=payload, timeout=10)
                
                if response.status_code == 204:
                    return True
                else:
                    error_msg = f"HTTP {response.status_code}"
                    if response.text:
                        error_msg += f": {response.text[:100]}"
                    
                    # Если это последняя попытка, логируем ошибку
                    if attempt == max_retries - 1:
                        logger.error(f"❌ Ошибка отправки события '{event_name}': {error_msg}")
                        return False
                    
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    logger.warning(f"⚠️  Попытка {attempt + 1}/{max_retries} не удалась, повтор через {wait_time}с...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                # Если это последняя попытка, логируем ошибку
                if attempt == max_retries - 1:
                    logger.error(f"❌ Ошибка при отправке события '{event_name}': {e}")
                    return False
                
                # Exponential backoff
                wait_time = 2 ** attempt
                logger.warning(f"⚠️  Попытка {attempt + 1}/{max_retries} не удалась, повтор через {wait_time}с...")
                time.sleep(wait_time)
        
        return False
    
    def register_event(
        self,
        event_name: str,
        description: Optional[str] = None,
        sample_parameters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Регистрирует событие в GA4, отправив тестовое событие
        
        Args:
            event_name: Название события
            description: Описание события (для логирования)
            sample_parameters: Примерные параметры для события (ограничиваются до 20)
        
        Returns:
            True если событие отправлено успешно
        """
        # Отправляем событие с минимальными параметрами (max 20)
        # Выбираем только самые важные параметры
        params = sample_parameters or {
            "event_category": "custom",
            "event_source": "script_registration",
            "registration_timestamp": datetime.now().isoformat()[:19]  # Без микросекунд
        }
        
        # Ограничиваем параметры до 20 (best practice)
        if len(params) > 20:
            # Берем первые 20 самых важных
            important_keys = list(params.keys())[:20]
            params = {k: params[k] for k in important_keys}
            logger.warning(f"⚠️  Параметры события '{event_name}' ограничены до 20")
        
        success = self.send_event(event_name, params)
        
        if success:
            logger.info(f"✅ Событие '{event_name}' отправлено в GA4")
            if description:
                logger.info(f"   Описание: {description}")
            logger.info(f"   Параметров: {len(params)}")
            logger.info(f"   ⏳ Событие появится в GA4 через несколько минут")
            logger.info(f"   📊 Проверьте в Real-time отчете GA4")
        
        return success
    
    def create_all_events(self, tier_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Создает все события из списка
        
        Args:
            tier_filter: Фильтр по tier ("Tier 1", "Tier 2", "Tier 3" или None для всех)
        
        Returns:
            Словарь с результатами создания
        """
        events = self.get_custom_events_list()
        
        # Фильтруем по tier если указан
        if tier_filter:
            events = [e for e in events if tier_filter in e["tier"]]
        
        results = {
            "total": len(events),
            "created": 0,
            "skipped": 0,
            "failed": 0,
            "events": []
        }
        
        logger.info(f"\n🚀 Начинаем создание {len(events)} событий...")
        logger.info(f"   Measurement ID: {self.measurement_id}\n")
        
        for event in events:
            event_name = event["event_name"]
            description = event.get("description", "")
            tier = event.get("tier", "")
            
            logger.info(f"📌 Регистрирую: {event_name} ({tier})")
            
            # Получаем примерные параметры из описания события
            # Ограничиваем до 15-20 параметров (best practice)
            sample_params = {}
            if "parameters" in event:
                # Берем только первые 15 параметров (safe zone)
                max_params = min(15, len(event["parameters"]))
                for param in event["parameters"][:max_params]:
                    # Создаем безопасные тестовые значения
                    if "email" in param.lower() or "phone" in param.lower():
                        # Не отправляем PII даже в тестовых данных
                        continue
                    sample_params[param] = f"test_{param[:20]}"  # Ограничиваем длину
            
            success = self.register_event(event_name, description, sample_params)
            
            # Rate limiting: задержка между запросами
            import time as time_module
            time_module.sleep(self.min_delay_between_requests)
            
            if success:
                results["created"] += 1
                results["events"].append({
                    "name": event_name,
                    "status": "sent",
                    "tier": tier
                })
            else:
                results["failed"] += 1
                results["events"].append({
                    "name": event_name,
                    "status": "failed",
                    "tier": tier
                })
            
            # Небольшая задержка между запросами
            import time
            time.sleep(0.5)
        
        logger.info(f"\n✅ Готово!")
        logger.info(f"   Создано: {results['created']}")
        logger.info(f"   Пропущено (уже существуют): {results['skipped']}")
        logger.info(f"   Всего: {results['total']}")
        
        return results


def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Регистрация custom events в GA4 через Measurement Protocol"
    )
    parser.add_argument(
        "--measurement-id",
        type=str,
        help="GA4 Measurement ID (G-XXXXXXXXXX) или установите GA4_MEASUREMENT_ID в .env"
    )
    parser.add_argument(
        "--api-secret",
        type=str,
        help="GA4 API Secret или установите GA4_API_SECRET в .env"
    )
    parser.add_argument(
        "--property-id",
        type=str,
        help="GA4 Property ID (для автоматического получения Measurement ID)"
    )
    parser.add_argument(
        "--credentials",
        type=str,
        help="Путь к JSON файлу Service Account"
    )
    parser.add_argument(
        "--tier",
        type=str,
        choices=["Tier 1", "Tier 2", "Tier 3"],
        help="Зарегистрировать события только определенного tier"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Показать список событий без регистрации (dry run)"
    )
    
    args = parser.parse_args()
    
    try:
        # Создаем экземпляр класса
        creator = GA4EventCreator(
            measurement_id=args.measurement_id,
            api_secret=args.api_secret,
            credentials_path=args.credentials,
            property_id=args.property_id
        )
        
        if args.dry_run:
            # Показываем список событий
            events = creator.get_custom_events_list()
            if args.tier:
                events = [e for e in events if args.tier in e["tier"]]
            
            print(f"\n📋 Список событий для создания ({len(events)}):\n")
            for event in events:
                print(f"  • {event['event_name']:30} | {event['tier']:20} | {event['category']:15}")
            print()
            return
        
        # Регистрируем события
        results = creator.create_all_events(tier_filter=args.tier)
        
        # Выводим итоговую статистику
        print("\n" + "="*60)
        print("ИТОГОВАЯ СТАТИСТИКА")
        print("="*60)
        print(f"Всего событий: {results['total']}")
        print(f"Отправлено: {results['created']}")
        print(f"Ошибок: {results['failed']}")
        print("="*60)
        print("\n💡 Следующие шаги:")
        print("1. Подождите 2-5 минут")
        print("2. Откройте GA4 → Reports → Real-time")
        print("3. Проверьте, что события появились")
        print("4. В Admin → Events настройте события как конверсии (если нужно)")
        print("="*60)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

