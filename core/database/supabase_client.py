"""
Supabase Database Client
Простая обертка для работы с Supabase PostgreSQL
"""

import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Глобальный клиент (singleton pattern)
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Получить Supabase клиент (singleton)
    
    Returns:
        Client: Supabase client instance
        
    Raises:
        ValueError: Если не заданы SUPABASE_URL или SUPABASE_KEY
    """
    global _supabase_client
    
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError(
                "SUPABASE_URL и SUPABASE_KEY должны быть установлены в .env файле"
            )
        
        _supabase_client = create_client(url, key)
    
    return _supabase_client


def get_admin_client() -> Client:
    """
    Получить Supabase клиент с service_role ключом (полные права)
    Используйте только для административных операций!
    
    Returns:
        Client: Supabase admin client
    """
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not service_key:
        raise ValueError(
            "SUPABASE_URL и SUPABASE_SERVICE_KEY должны быть установлены"
        )
    
    return create_client(url, service_key)


# ===================================
# Простые функции для работы с данными
# ===================================

def create_record(table: str, data: dict) -> dict:
    """Создать запись в таблице"""
    supabase = get_supabase_client()
    result = supabase.table(table).insert(data).execute()
    return result.data[0] if result.data else {}


def get_record(table: str, record_id: str) -> Optional[dict]:
    """Получить запись по ID"""
    supabase = get_supabase_client()
    result = supabase.table(table).select("*").eq("id", record_id).execute()
    return result.data[0] if result.data else None


def get_records(table: str, limit: int = 100, filters: Optional[dict] = None) -> list:
    """
    Получить записи из таблицы
    
    Args:
        table: Название таблицы
        limit: Лимит записей
        filters: Словарь фильтров {"column": "value"}
    """
    supabase = get_supabase_client()
    query = supabase.table(table).select("*")
    
    if filters:
        for column, value in filters.items():
            query = query.eq(column, value)
    
    result = query.limit(limit).execute()
    return result.data


def update_record(table: str, record_id: str, data: dict) -> dict:
    """Обновить запись"""
    supabase = get_supabase_client()
    result = supabase.table(table).update(data).eq("id", record_id).execute()
    return result.data[0] if result.data else {}


def delete_record(table: str, record_id: str) -> bool:
    """Удалить запись"""
    supabase = get_supabase_client()
    result = supabase.table(table).delete().eq("id", record_id).execute()
    return len(result.data) > 0


# ===================================
# Специфичные функции для бизнес-логики
# ===================================

def create_lead(ad_id: str, name: str, phone: str, source: str, **kwargs) -> dict:
    """
    Создать нового лида
    
    Args:
        ad_id: ID объявления
        name: Имя лида
        phone: Телефон
        source: Источник (whatsapp, telegram, etc)
        **kwargs: Дополнительные поля
    """
    data = {
        "ad_id": ad_id,
        "name": name,
        "phone": phone,
        "source": source,
        "status": "new",
        **kwargs
    }
    return create_record("leads", data)


def update_lead_status(lead_id: str, status: str) -> dict:
    """Обновить статус лида"""
    return update_record("leads", lead_id, {"status": status})


def add_conversation_message(
    lead_id: str, 
    message: str, 
    sender: str, 
    platform: str
) -> dict:
    """
    Добавить сообщение в историю общения
    
    Args:
        lead_id: ID лида
        message: Текст сообщения
        sender: bot, lead или human
        platform: whatsapp, telegram
    """
    data = {
        "lead_id": lead_id,
        "message": message,
        "sender": sender,
        "platform": platform
    }
    return create_record("conversations", data)


def get_lead_conversations(lead_id: str) -> list:
    """Получить все сообщения лида"""
    supabase = get_supabase_client()
    result = supabase.table("conversations")\
        .select("*")\
        .eq("lead_id", lead_id)\
        .order("created_at", desc=False)\
        .execute()
    return result.data


def get_campaign_stats(campaign_id: str) -> dict:
    """
    Получить статистику по кампании
    
    Returns:
        dict: {'ads_count', 'leads_count', 'cpl', 'roi'}
    """
    supabase = get_supabase_client()
    
    # Получить кампанию
    campaign = get_record("campaigns", campaign_id)
    if not campaign:
        return {}
    
    # Получить объявления
    ads = get_records("ads", filters={"campaign_id": campaign_id})
    
    # Получить лиды
    ad_ids = [ad["id"] for ad in ads]
    leads = []
    for ad_id in ad_ids:
        leads.extend(get_records("leads", filters={"ad_id": ad_id}))
    
    # Расчет метрик
    ads_count = len(ads)
    leads_count = len(leads)
    spent = campaign.get("spent", 0)
    cpl = round(spent / leads_count, 2) if leads_count > 0 else 0
    
    return {
        "ads_count": ads_count,
        "leads_count": leads_count,
        "spent": spent,
        "cpl": cpl,
        "qualified_leads": len([l for l in leads if l["status"] == "qualified"]),
        "hot_leads": len([l for l in leads if l["status"] == "hot"]),
        "won_leads": len([l for l in leads if l["status"] == "won"])
    }


# ===================================
# Экспорт
# ===================================

__all__ = [
    "get_supabase_client",
    "get_admin_client",
    "create_record",
    "get_record",
    "get_records",
    "update_record",
    "delete_record",
    "create_lead",
    "update_lead_status",
    "add_conversation_message",
    "get_lead_conversations",
    "get_campaign_stats"
]

