# utils/logging_setup.py
import logging
import sys
from datetime import datetime
from config.settings import Config

def setup_logging():
    """Configure logging with both file and console handlers"""
    # Ensure log directory exists
    Config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create timestamp for log files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Configure basic logging
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_DIR / f"jira_categorizer_{timestamp}.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Add separate error log handler
    error_handler = logging.FileHandler(Config.LOG_DIR / f"errors_{timestamp}.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    ))
    logging.getLogger().addHandler(error_handler)
    
    # Set OpenAI and related loggers to WARNING level
    loggers_to_quiet = [
        "openai",
        "openai.http_client",
        "openai._client",
        "httpx",
        "httpcore"
    ]
    
    for logger_name in loggers_to_quiet:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)
    
    logging.info("Logging configured successfully")