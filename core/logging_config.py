import logging
import logging.handlers
import os
from datetime import datetime
from core.config import get_settings

def setup_logging():
    """Setup logging configuration"""
    settings = get_settings()
    
    # Create logs directory if it doesn't exist
    os.makedirs(settings.LOGS_DIR, exist_ok=True)
    
    # Configure logging
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Set the root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    log_file_path = os.path.join(settings.LOGS_DIR, settings.LOG_FILE)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler (for errors only)
    error_log_path = os.path.join(settings.LOGS_DIR, "error.log")
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_path,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logging.info("Logging system initialized")

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)

# Custom logging middleware for FastAPI
class LoggingMiddleware:
    """Custom logging middleware to log API requests"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger("api_requests")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = datetime.now()
            
            # Log request
            self.logger.info(
                f"Request: {scope['method']} {scope['path']} "
                f"from {scope.get('client', ['unknown'])[0]}"
            )
            
            # Process request
            await self.app(scope, receive, send)
            
            # Log response time
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Request completed in {duration:.2f}s")
        else:
            await self.app(scope, receive, send)