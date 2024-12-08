import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from colorama import Fore, Style
from src.config.settings import Settings

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels"""
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, '')
        record.msg = f"{color}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

class Logger:
    def __init__(self):
        self.logger = self.setup_logger()

    def setup_logger(self):
        """Configure and return a logger instance."""
        # Create logs directory if it doesn't exist
        os.makedirs(Settings.LOGS_DIR, exist_ok=True)

        # Configure logging
        logger = logging.getLogger('SMTPManager')
        logger.setLevel(logging.DEBUG)

        # Clear any existing handlers
        logger.handlers = []

        # File handler with rotation
        file_handler = RotatingFileHandler(
            Settings.LOG_FILE,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console handler with colors
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter()
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        return logger

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

def setup_logger():
    """Create and return a configured logger instance."""
    logger = Logger()
    return logger.logger