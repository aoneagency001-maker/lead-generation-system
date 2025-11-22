"""
Bot Detector
Определение ботов и поисковых роботов
"""

import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class BotDetector:
    """Определение ботов по User-Agent"""
    
    # Список известных ботов
    BOT_PATTERNS = [
        r'googlebot',
        r'bingbot',
        r'slurp',  # Yahoo
        r'duckduckbot',
        r'baiduspider',
        r'yandexbot',
        r'sogou',
        r'exabot',
        r'facebot',
        r'ia_archiver',
        r'facebookexternalhit',
        r'twitterbot',
        r'rogerbot',
        r'linkedinbot',
        r'embedly',
        r'quora link preview',
        r'showyoubot',
        r'outbrain',
        r'pinterest',
        r'slackbot',
        r'vkShare',
        r'W3C_Validator',
        r'whatsapp',
        r'flipboard',
        r'tumblr',
        r'bitlybot',
        r'skypeuripreview',
        r'nuzzel',
        r'redditbot',
        r'Applebot',
        r'flipboard',
        r'bitlybot',
        r'bitly',
        r'headless',
        r'phantom',
        r'puppeteer',
        r'selenium',
        r'webdriver',
        r'curl',
        r'wget',
        r'python-requests',
        r'postman',
        r'insomnia',
        r'httpie',
        r'go-http-client',
        r'java',
        r'okhttp',
        r'apache-httpclient',
        r'bot',
        r'crawler',
        r'spider',
        r'scraper',
    ]
    
    def __init__(self):
        # Компилируем паттерны один раз
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.BOT_PATTERNS]
    
    def is_bot(self, user_agent: Optional[str] = None) -> bool:
        """
        Определить является ли User-Agent ботом
        
        Args:
            user_agent: User-Agent строка
        
        Returns:
            True если это бот
        """
        if not user_agent:
            return False
        
        user_agent_lower = user_agent.lower()
        
        # Проверяем каждый паттерн
        for pattern in self.patterns:
            if pattern.search(user_agent_lower):
                logger.debug(f"Bot detected: {user_agent[:50]}...")
                return True
        
        return False
    
    def get_device_type(self, user_agent: Optional[str] = None) -> str:
        """
        Определить тип устройства
        
        Args:
            user_agent: User-Agent строка
        
        Returns:
            'mobile', 'tablet' или 'desktop'
        """
        if not user_agent:
            return "desktop"
        
        user_agent_lower = user_agent.lower()
        
        # Мобильные устройства
        mobile_patterns = [
            r'mobile',
            r'android',
            r'iphone',
            r'ipod',
            r'blackberry',
            r'windows phone',
            r'opera mini',
        ]
        
        # Планшеты
        tablet_patterns = [
            r'ipad',
            r'android(?!.*mobile)',
            r'kindle',
            r'silk',
            r'playbook',
        ]
        
        # Проверяем планшеты
        for pattern in tablet_patterns:
            if re.search(pattern, user_agent_lower, re.IGNORECASE):
                return "tablet"
        
        # Проверяем мобильные
        for pattern in mobile_patterns:
            if re.search(pattern, user_agent_lower, re.IGNORECASE):
                return "mobile"
        
        return "desktop"

