import logging
import logging.handlers
from config import Config

def setup_logging():
    """Setup logging based on configuration."""
    # Create logs directory
    Config.ensure_directories()
    
    # Configure logging level
    level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if Config.LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if Config.LOG_TO_FILE:
        log_file = f"{Config.LOG_DIRECTORY}/westermo.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=Config.MAX_LOG_SIZE_MB * 1024 * 1024,
            backupCount=Config.LOG_BACKUP_COUNT
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
