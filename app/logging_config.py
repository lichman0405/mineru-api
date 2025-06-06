# app/logging_config.py

import logging
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler
import os

def setup_logging():
    """
    Configures logging for the application with both file and console handlers.
    """
    LOG_DIR = "/app/data/logs"
    LOG_FILE = os.path.join(LOG_DIR, "app.log")
    LOG_LEVEL = "INFO"
    
    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Define the format for file logs (more detailed)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Define the handler for file output with rotation
    # 5MB per file, keep last 5 backup files
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    
    # Define the handler for rich console output (less detailed, more readable)
    console_handler = RichHandler(
        rich_tracebacks=True,
        show_path=False, # Don't show file path, it's long in Docker
        markup=True # Allow rich markup like [bold]
    )
    # The console handler will use its own beautiful formatting by default

    # Get the root logger and configure it
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    
    # Avoid adding handlers multiple times in dev environments with hot-reloading
    if not root_logger.hasHandlers():
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    logging.getLogger("uvicorn.access").disabled = True 

    root_logger.info("Logging configured successfully. Ready to log.")