"""
Сервис сегментации поисковых запросов
Разбивает запросы на группы по "намерению" и "горячести"
"""

from enum import Enum
from typing import Dict, List, Optional


class SearchSegment(Enum):
    """Типы сегментов поисковых запросов"""
    BRAND = "Бренд"  # "vessel group", "vesselgroup"
    PRODUCT = "Продукт"  # "крыша алматы", "кровельные материалы"
    PROBLEM = "Проблема/Боль"  # "ремонт кровли", "утечка"
    DECISION = "Решение"  # "какой производитель лучше", "цены"
    COMPARISON = "Сравнение"  # "марки vs марки", "бренды"
    URGENCY = "Высокая спешка"  # "купить сейчас", "срочно"
    INFORMATIONAL = "Информационный"  # "что такое", "как выбрать"
    LOCATION = "Географический"  # "в алматы", "казахстан"


class SearchSegmentationEngine:
    """Разбивает запросы на сегменты для целевой аналитики"""

    def __init__(self):
        # Ключевые слова для каждого сегмента
        self.keywords = {
            SearchSegment.BRAND: [
                "vessel group", "vesselgroup", "vessel roof", "vessel",
                "марка", "бренд", "производитель", "компания"
            ],
            SearchSegment.PRODUCT: [
                "кровля", "кровельные", "черепица", "крыша",
                "метал черепица", "материалы", "товар", "продукт",
                "металлочерепица", "профнастил", "ондулин"
            ],
            SearchSegment.PROBLEM: [
                "ремонт", "утечка", "протечка", "сломалась",
                "проблема", "дефект", "поломка", "течет",
                "повреждение", "неисправность"
            ],
            SearchSegment.DECISION: [
                "какой", "какая", "лучше", "цена", "стоимость",
                "где купить", "как выбрать", "отзывы", "рейтинг",
                "сколько стоит", "прайс", "цены"
            ],
            SearchSegment.COMPARISON: [
                "vs", "или", "сравнение", "разница",
                "отличие", "сравнить", "против", "лучше чем"
            ],
            SearchSegment.URGENCY: [
                "срочно", "быстро", "сейчас", "сегодня",
                "немедленно", "асап", "купить сейчас", "заказать",
                "быстрая доставка", "срочный ремонт"
            ],
            SearchSegment.LOCATION: [
                "алматы", "астана", "казахстан", "кз",
                "в городе", "местный", "рядом", "алмата",
                "нур-султан", "шымкент"
            ],
            SearchSegment.INFORMATIONAL: [
                "что такое", "как", "какой", "виды",
                "типы", "информация", "статья", "обзор",
                "характеристики", "описание"
            ]
        }

    def classify_query(self, query: str) -> List[SearchSegment]:
        """
        Классифицирует запрос в один или несколько сегментов
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Список сегментов, к которым относится запрос
        """
        if not query:
            return [SearchSegment.INFORMATIONAL]
        
        query_lower = query.lower().strip()
        segments = []
        
        # Проверяем каждый сегмент
        for segment, keywords in self.keywords.items():
            if any(kw in query_lower for kw in keywords):
                segments.append(segment)
        
        # Если не совпадает ни с чем — "информационный"
        if not segments:
            segments.append(SearchSegment.INFORMATIONAL)
        
        return segments

    def get_segment_heat_score(
        self,
        segment: SearchSegment,
        visits: int
    ) -> Dict[str, any]:
        """
        Определяет "температуру" сегмента (насколько горячий лид)
        
        Args:
            segment: Сегмент запроса
            visits: Количество визитов
            
        Returns:
            Словарь с данными о горячести:
            {
                "segment": "Высокая спешка",
                "priority": 1.5,
                "heat_visits": 150.0,
                "color": "#ff4444"
            }
        """
        segment_priority = {
            SearchSegment.URGENCY: 1.5,  # Самый горячий
            SearchSegment.DECISION: 1.3,
            SearchSegment.PROBLEM: 1.2,
            SearchSegment.PRODUCT: 1.0,
            SearchSegment.COMPARISON: 0.9,
            SearchSegment.LOCATION: 0.8,
            SearchSegment.BRAND: 0.7,
            SearchSegment.INFORMATIONAL: 0.5  # Холодный
        }
        
        priority = segment_priority.get(segment, 1.0)
        
        return {
            "segment": segment.value,
            "priority": priority,
            "heat_visits": visits * priority,
            "color": self._get_segment_color(segment)
        }

    def _get_segment_color(self, segment: SearchSegment) -> str:
        """
        Возвращает цвет для визуализации сегмента
        
        Args:
            segment: Сегмент
            
        Returns:
            HEX цвет
        """
        colors = {
            SearchSegment.URGENCY: "#ff4444",  # Красный (очень горячий)
            SearchSegment.DECISION: "#ff8844",  # Оранжевый
            SearchSegment.PROBLEM: "#ffbb44",  # Жёлтый
            SearchSegment.PRODUCT: "#44bb44",  # Зелёный
            SearchSegment.COMPARISON: "#4488ff",  # Синий
            SearchSegment.LOCATION: "#8844ff",  # Фиолетовый
            SearchSegment.BRAND: "#cccccc",  # Серый
            SearchSegment.INFORMATIONAL: "#999999"  # Тёмно-серый
        }
        return colors.get(segment, "#cccccc")

