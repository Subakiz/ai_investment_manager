"""
Logging configuration for AlphaGen Investment Platform
"""
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from datetime import datetime
import sys

from ..config.settings import config

class Logger:
    """Custom logger class for the application"""
    
    def __init__(self, name: str = "alphagen"):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with file and console handlers"""
        self.logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for all logs
        log_file = config.LOGS_DIR / f"{self.name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # Error file handler
        error_file = config.LOGS_DIR / f"{self.name}_error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance"""
        return self.logger

class DataPipelineLogger(Logger):
    """Specialized logger for data pipeline operations"""
    
    def __init__(self):
        super().__init__("data_pipeline")
        self._setup_pipeline_handlers()
    
    def _setup_pipeline_handlers(self):
        """Setup additional handlers for data pipeline"""
        # Market data handler
        market_file = config.LOGS_DIR / "market_data.log"
        market_handler = logging.handlers.RotatingFileHandler(
            market_file,
            maxBytes=10*1024*1024,
            backupCount=10
        )
        market_handler.setLevel(logging.INFO)
        market_handler.setFormatter(logging.Formatter(
            '%(asctime)s - MARKET - %(levelname)s - %(message)s'
        ))
        
        # News data handler
        news_file = config.LOGS_DIR / "news_data.log"
        news_handler = logging.handlers.RotatingFileHandler(
            news_file,
            maxBytes=10*1024*1024,
            backupCount=10
        )
        news_handler.setLevel(logging.INFO)
        news_handler.setFormatter(logging.Formatter(
            '%(asctime)s - NEWS - %(levelname)s - %(message)s'
        ))
        
        # Add filters to route messages to appropriate handlers
        class MarketFilter(logging.Filter):
            def filter(self, record):
                return 'market' in record.getMessage().lower()
        
        class NewsFilter(logging.Filter):
            def filter(self, record):
                return 'news' in record.getMessage().lower()
        
        market_handler.addFilter(MarketFilter())
        news_handler.addFilter(NewsFilter())
        
        self.logger.addHandler(market_handler)
        self.logger.addHandler(news_handler)

def get_logger(name: str = "alphagen") -> logging.Logger:
    """Get a logger instance"""
    logger_instance = Logger(name)
    return logger_instance.get_logger()

def get_pipeline_logger() -> logging.Logger:
    """Get a specialized logger for data pipeline operations"""
    logger_instance = DataPipelineLogger()
    return logger_instance.get_logger()

# Create default logger instances
default_logger = get_logger()
pipeline_logger = get_pipeline_logger()