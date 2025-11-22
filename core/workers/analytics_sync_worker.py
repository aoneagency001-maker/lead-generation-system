"""
Analytics Sync Worker
Воркер для автоматической синхронизации данных из аналитики в БД

Запускает pipeline для обработки данных:
- L1 (Raw): Сырые данные из API
- L2 (Normalized): Нормализованные данные
- L3 (Features): Вычисленные фичи

Использование:
    # Запуск воркера
    python -m core.workers.analytics_sync_worker
    
    # Или через asyncio
    import asyncio
    from core.workers.analytics_sync_worker import run_sync_worker
    asyncio.run(run_sync_worker())
"""

import asyncio
import logging
from datetime import date, timedelta
from typing import Optional
import os

from data_intake.pipeline import DataIntakePipeline
from data_intake.models import SourceType
from core.api.config import settings

logger = logging.getLogger(__name__)

# Интервал синхронизации (по умолчанию 1 час)
SYNC_INTERVAL_SECONDS = int(os.getenv("ANALYTICS_SYNC_INTERVAL", 3600))

# Количество дней для синхронизации (по умолчанию последние 7 дней)
SYNC_DAYS = int(os.getenv("ANALYTICS_SYNC_DAYS", 7))


class AnalyticsSyncWorker:
    """
    Воркер для автоматической синхронизации данных аналитики.
    
    Периодически запускает pipeline для обработки данных из:
    - Яндекс.Метрика
    - Google Analytics 4
    """
    
    def __init__(self):
        self.pipeline = DataIntakePipeline()
        self.running = False
        self.sync_interval = SYNC_INTERVAL_SECONDS
        self.sync_days = SYNC_DAYS
    
    async def sync_source(self, source: SourceType) -> bool:
        """
        Синхронизировать данные из одного источника.
        
        Args:
            source: Тип источника (YANDEX_METRIKA или GOOGLE_ANALYTICS)
        
        Returns:
            True если успешно, False если ошибка
        """
        try:
            date_to = date.today()
            date_from = date_to - timedelta(days=self.sync_days)
            
            logger.info(
                f"🔄 Начинаю синхронизацию {source.value}: "
                f"{date_from} - {date_to}"
            )
            
            # Запускаем pipeline
            status = await self.pipeline.run_full_pipeline(
                source=source,
                date_from=date_from,
                date_to=date_to
            )
            
            if status.status == "completed":
                logger.info(
                    f"✅ Синхронизация {source.value} завершена: "
                    f"raw={status.raw_count}, normalized={status.normalized_count}, "
                    f"features={status.features_count}"
                )
                return True
            else:
                logger.error(
                    f"❌ Синхронизация {source.value} не завершена: "
                    f"status={status.status}, errors={len(status.errors)}"
                )
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка синхронизации {source.value}: {e}", exc_info=True)
            return False
    
    async def sync_all_sources(self) -> dict[SourceType, bool]:
        """
        Синхронизировать данные из всех доступных источников.
        
        Returns:
            dict: Результаты синхронизации для каждого источника
        """
        results = {}
        
        # Синхронизируем Яндекс.Метрику
        if SourceType.YANDEX_METRIKA in self.pipeline.providers:
            results[SourceType.YANDEX_METRIKA] = await self.sync_source(
                SourceType.YANDEX_METRIKA
            )
        else:
            logger.warning("⚠️ Яндекс.Метрика провайдер не зарегистрирован")
            results[SourceType.YANDEX_METRIKA] = False
        
        # Синхронизируем Google Analytics 4
        if SourceType.GOOGLE_ANALYTICS in self.pipeline.providers:
            results[SourceType.GOOGLE_ANALYTICS] = await self.sync_source(
                SourceType.GOOGLE_ANALYTICS
            )
        else:
            logger.warning("⚠️ Google Analytics провайдер не зарегистрирован")
            results[SourceType.GOOGLE_ANALYTICS] = False
        
        return results
    
    async def run(self):
        """
        Запустить воркер в бесконечном цикле.
        """
        self.running = True
        logger.info(
            f"🚀 Analytics Sync Worker запущен: "
            f"interval={self.sync_interval}s, days={self.sync_days}"
        )
        
        while self.running:
            try:
                # Синхронизируем все источники
                results = await self.sync_all_sources()
                
                # Логируем результаты
                success_count = sum(1 for success in results.values() if success)
                total_count = len(results)
                
                logger.info(
                    f"📊 Синхронизация завершена: "
                    f"{success_count}/{total_count} источников успешно"
                )
                
            except Exception as e:
                logger.error(f"❌ Критическая ошибка в воркере: {e}", exc_info=True)
            
            # Ждем перед следующей синхронизацией
            logger.info(f"⏳ Ожидание {self.sync_interval} секунд до следующей синхронизации...")
            await asyncio.sleep(self.sync_interval)
    
    def stop(self):
        """Остановить воркер."""
        self.running = False
        logger.info("🛑 Analytics Sync Worker остановлен")


async def run_sync_worker():
    """
    Запустить воркер синхронизации.
    
    Использование:
        import asyncio
        from core.workers.analytics_sync_worker import run_sync_worker
        asyncio.run(run_sync_worker())
    """
    worker = AnalyticsSyncWorker()
    
    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки (Ctrl+C)")
        worker.stop()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        worker.stop()
        raise


if __name__ == "__main__":
    # Запуск воркера напрямую
    asyncio.run(run_sync_worker())

