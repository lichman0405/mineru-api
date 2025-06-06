# app/logging_config.py

# app/logging_config.py (final version)

import logging
import os
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler

def setup_logging():
    LOG_DIR = "/app/data/logs"
    LOG_FILE = os.path.join(LOG_DIR, "app.log")
    LOG_LEVEL = "INFO"
    
    os.makedirs(LOG_DIR, exist_ok=True)
    
    file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, 
        backupCount=5, 
        encoding='utf-8'
        )
    file_handler.setFormatter(file_formatter)
    
    console_handler = RichHandler(
        rich_tracebacks=True, 
        show_path=False, 
        markup=True
        )

    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    
    if not root_logger.hasHandlers():
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    logging.getLogger("uvicorn.access").disabled = True
    root_logger.info("Logging configured successfully. Ready to log.")