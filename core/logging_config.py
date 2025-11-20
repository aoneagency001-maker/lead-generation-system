"""
Centralized logging configuration for the entire application

Usage:
    from core.logging_config import setup_logging
    
    logger = setup_logging()
    logger.info("Application started")
    logger.error("Error occurred", exc_info=True)
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    app_name: str = "lead_generation"
) -> logging.Logger:
    """
    Setup centralized logging with console and file handlers
    
    Features:
    - Console output (colored if possible)
    - Rotating file handler (10MB per file, 5 backups)
    - Separate error log
    - Timestamp in filenames
    - UTF-8 encoding (для русского языка)
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files
        app_name: Application name for log files
    
    Returns:
        logging.Logger: Configured root logger
    """
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Format
    detailed_format = logging.Formatter(
        '%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_format = logging.Formatter(
        '%(levelname)-8s | %(message)s'
    )
    
    # 1. Console Handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_format)
    root_logger.addHandler(console_handler)
    
    # 2. Main Log File (rotating, INFO and above)
    main_log_file = log_path / f"{app_name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        main_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_format)
    root_logger.addHandler(file_handler)
    
    # 3. Error Log File (ERROR and above only)
    error_log_file = log_path / f"{app_name}_errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_format)
    root_logger.addHandler(error_handler)
    
    # 4. Debug Log File (if DEBUG mode)
    if log_level.upper() == "DEBUG":
        debug_log_file = log_path / f"{app_name}_debug.log"
        debug_handler = logging.handlers.RotatingFileHandler(
            debug_log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=3,
            encoding='utf-8'
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(detailed_format)
        root_logger.addHandler(debug_handler)
    
    # Log startup message
    root_logger.info("=" * 80)
    root_logger.info(f"🚀 Logging initialized | Level: {log_level} | Dir: {log_dir}")
    root_logger.info("=" * 80)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger (use in modules)
    
    Usage:
        from core.logging_config import get_logger
        
        logger = get_logger(__name__)
        logger.info("Module started")
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        logging.Logger: Named logger
    """
    return logging.getLogger(name)


# === Module-specific loggers ===

def get_module_logger(module_name: str) -> logging.Logger:
    """
    Get a logger for a specific module
    
    Args:
        module_name: Module name (e.g., "olx_parser", "telegram_bot")
    
    Returns:
        logging.Logger: Module logger
    """
    logger = logging.getLogger(f"modules.{module_name}")
    return logger


# === Error notification helper ===

async def log_and_notify_error(
    logger: logging.Logger,
    error: Exception,
    context: str,
    notify_admin: bool = True
):
    """
    Log error and optionally notify admin via Telegram
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Context where error happened
        notify_admin: Whether to send Telegram notification
    """
    error_msg = f"ERROR in {context}: {type(error).__name__}: {str(error)}"
    logger.error(error_msg, exc_info=True)
    
    if notify_admin:
        try:
            from shared.telegram_notifier import send_error_notification
            await send_error_notification(error, context)
        except Exception as e:
            logger.warning(f"Failed to send error notification: {e}")


# === Usage Examples ===

if __name__ == "__main__":
    # Example 1: Basic setup
    logger = setup_logging(log_level="INFO")
    
    logger.info("This is an info message")
    logger.warning("This is a warning")
    logger.error("This is an error")
    
    # Example 2: Module logger
    module_logger = get_module_logger("olx_parser")
    module_logger.info("OLX parser started")
    
    # Example 3: With exception
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.error("Error occurred", exc_info=True)
    
    print("\n✅ Check logs/ directory for log files")

