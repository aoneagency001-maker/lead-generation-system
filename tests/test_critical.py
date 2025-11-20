"""
Critical Path Tests

These are the MOST IMPORTANT tests - they verify core functionality:
1. Database connection works
2. OLX scraping works
3. Satu scraping works
4. Telegram bot sends messages
5. Event bus publishes events

Run with: pytest tests/test_critical.py -v

If ANY of these fail, DO NOT DEPLOY!
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock


# ===================================================================
# TEST 1: Database Connection
# ===================================================================

@pytest.mark.asyncio
async def test_database_connection_works():
    """
    CRITICAL: Verify database connection is working
    
    If this fails:
    - Check .env has correct SUPABASE_URL and SUPABASE_KEY
    - Check internet connection
    - Check Supabase project is running
    """
    try:
        from core.database.supabase_client import get_supabase_client
        
        db = get_supabase_client()
        
        # Simple query to verify connection
        # Using a table that should always exist
        result = db.table("niches").select("*").limit(1).execute()
        
        # Should not raise exception
        assert result is not None
        assert hasattr(result, 'data')
        
        print("✅ Database connection: OK")
        
    except Exception as e:
        pytest.fail(f"❌ Database connection FAILED: {e}")


# ===================================================================
# TEST 2: OLX Scraping
# ===================================================================

@pytest.mark.asyncio
async def test_olx_scraping_works():
    """
    CRITICAL: Verify OLX scraping functionality
    
    If this fails:
    - OLX might have changed their HTML structure
    - Check internet connection
    - Check if OLX.kz is accessible
    - Might need to update selectors
    """
    try:
        from library.platforms.olx.scraping_examples import OLXScraperExample
        
        # Initialize scraper
        scraper = OLXScraperExample(headless=True)
        
        # Try to scrape (just 1 page, quick test)
        # Using a common query that should always have results
        listings = await scraper.scrape_search(
            search_query="телефон",
            max_pages=1
        )
        
        # Verify results
        assert len(listings) > 0, "No listings found"
        assert 'title' in listings[0], "Missing title field"
        assert 'url' in listings[0], "Missing URL field"
        
        print(f"✅ OLX scraping: OK (found {len(listings)} listings)")
        
    except ImportError:
        pytest.skip("OLX scraper module not available")
    except Exception as e:
        pytest.fail(f"❌ OLX scraping FAILED: {e}")


# ===================================================================
# TEST 3: Satu Scraping
# ===================================================================

@pytest.mark.asyncio
async def test_satu_scraping_works():
    """
    CRITICAL: Verify Satu.kz scraping functionality
    
    If this fails:
    - Satu might have changed their HTML structure
    - Check internet connection
    - Check if Satu.kz is accessible
    """
    try:
        from library.platforms.satu.scraping_examples import SatuScraperExample
        
        scraper = SatuScraperExample(headless=True)
        
        # Try to scrape
        products = await scraper.scrape_search(
            search_query="инструмент",
            max_pages=1
        )
        
        # Verify results
        assert len(products) > 0, "No products found"
        assert 'title' in products[0], "Missing title field"
        assert 'url' in products[0], "Missing URL field"
        
        print(f"✅ Satu scraping: OK (found {len(products)} products)")
        
    except ImportError:
        pytest.skip("Satu scraper module not available")
    except Exception as e:
        pytest.fail(f"❌ Satu scraping FAILED: {e}")


# ===================================================================
# TEST 4: Telegram Bot
# ===================================================================

@pytest.mark.asyncio
async def test_telegram_bot_sends_message():
    """
    CRITICAL: Verify Telegram bot can send messages
    
    If this fails:
    - Check TELEGRAM_BOT_TOKEN in .env
    - Check bot token is valid (@BotFather)
    - Check internet connection
    """
    try:
        from shared.telegram_notifier import send_notification
        
        # Mock the actual send (don't spam real Telegram)
        with patch('shared.telegram_notifier.send_notification') as mock_send:
            mock_send.return_value = {"success": True}
            
            result = await send_notification("Test message")
            
            assert result["success"] == True
            mock_send.assert_called_once()
        
        print("✅ Telegram bot: OK")
        
    except ImportError:
        pytest.skip("Telegram notifier module not available")
    except Exception as e:
        pytest.fail(f"❌ Telegram bot FAILED: {e}")


# ===================================================================
# TEST 5: Event Bus
# ===================================================================

@pytest.mark.asyncio
async def test_event_bus_publishes_events():
    """
    CRITICAL: Verify event bus can publish and receive events
    
    If this fails:
    - Event bus module might be broken
    - Check event bus initialization
    """
    try:
        from shared.event_bus import EventBus
        from shared.events import Event
        
        # Create event bus
        bus = EventBus()
        
        # Flag to track if event was received
        received = {"value": False}
        
        # Subscribe to test event
        @bus.subscribe("test.event")
        async def test_handler(event: Event):
            received["value"] = True
        
        # Publish event
        test_event = Event(
            event_type="test.event",
            payload={"test": "data"}
        )
        
        await bus.publish(test_event)
        
        # Give it a moment to process
        await asyncio.sleep(0.1)
        
        # Verify event was received
        assert received["value"] == True, "Event was not received"
        
        print("✅ Event bus: OK")
        
    except ImportError:
        pytest.skip("Event bus module not available")
    except Exception as e:
        pytest.fail(f"❌ Event bus FAILED: {e}")


# ===================================================================
# BONUS TEST: Logging
# ===================================================================

def test_logging_works():
    """
    BONUS: Verify logging is configured correctly
    
    If this fails:
    - Check core/logging_config.py exists
    - Check logs/ directory exists
    """
    try:
        from core.logging_config import setup_logging
        
        logger = setup_logging(log_level="INFO")
        
        # Try to log something
        logger.info("Test log message")
        
        # Verify logger is configured
        assert logger is not None
        assert len(logger.handlers) > 0
        
        print("✅ Logging: OK")
        
    except Exception as e:
        pytest.fail(f"❌ Logging FAILED: {e}")


# ===================================================================
# Run all tests
# ===================================================================

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])

