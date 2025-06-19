"""
MSBot Logging Configuration
Structured logging setup with JSON format support
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from app.config.settings import get_settings

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        
        # Create log entry dictionary
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)

class StandardFormatter(logging.Formatter):
    """Standard text formatter"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

def setup_logger(name: str) -> logging.Logger:
    """
    Setup and configure logger with structured formatting
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    settings = get_settings()
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Prevent adding multiple handlers
    if logger.handlers:
        return logger
    
    # Set log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Set formatter based on configuration
    if settings.log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = StandardFormatter()
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger

def log_with_extra(logger: logging.Logger, level: str, message: str, **extra_fields):
    """
    Log message with extra fields
    
    Args:
        logger: Logger instance
        level: Log level (info, warning, error, etc.)
        message: Log message
        **extra_fields: Additional fields to include in log
    """
    
    # Create a custom log record with extra fields
    log_func = getattr(logger, level.lower())
    
    # Create a temporary record to add extra fields
    record = logging.LogRecord(
        name=logger.name,
        level=getattr(logging, level.upper()),
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    record.extra_fields = extra_fields
    
    log_func(message, extra={"extra_fields": extra_fields})

# Bot-specific logging helpers
def log_teams_activity(logger: logging.Logger, activity_type: str, user_id: str = None, message: str = None):
    """Log Teams activity with structured data"""
    log_with_extra(
        logger, "info", f"Teams activity: {activity_type}",
        activity_type=activity_type,
        user_id=user_id,
        message_preview=message[:100] if message else None,
        component="teams_handler"
    )

def log_handler_execution(logger: logging.Logger, handler_name: str, execution_time: float, success: bool):
    """Log handler execution metrics"""
    log_with_extra(
        logger, "info" if success else "error", 
        f"Handler {handler_name} {'completed' if success else 'failed'}",
        handler_name=handler_name,
        execution_time_ms=round(execution_time * 1000, 2),
        success=success,
        component="handler_system"
    )