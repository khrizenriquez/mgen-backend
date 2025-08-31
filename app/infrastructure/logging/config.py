"""
Structured logging configuration for the donation management system.
Provides JSON-formatted logging with correlation IDs, PII masking, and unified app/access logs.
"""
import logging
import logging.config
import os
import sys
from typing import Any, Dict

import structlog
from pythonjsonlogger import jsonlogger

from .formatters import PIIMasker


class CorrelationFilter(logging.Filter):
    """Add correlation ID to log records if available"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Try to get correlation ID from context
        correlation_id = getattr(record, 'correlation_id', None)
        if not correlation_id:
            # Try to get from structlog context variables
            try:
                import structlog.contextvars
                correlation_id = structlog.contextvars.get_contextvars().get('request_id', 'N/A')
            except (RuntimeError, AttributeError, ImportError):
                correlation_id = 'N/A'
        
        record.correlation_id = correlation_id
        return True


class CustomJSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with PII masking and consistent field names"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pii_masker = PIIMasker()
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record"""
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = self.formatTime(record)
        log_record['level'] = record.levelname
        log_record['service'] = os.getenv('SERVICE_NAME', 'donations-api')
        log_record['env'] = os.getenv('ENVIRONMENT', 'development')
        log_record['version'] = os.getenv('VERSION', '1.0.0')
        log_record['logger'] = record.name
        
        # Add correlation ID
        log_record['request_id'] = getattr(record, 'correlation_id', 'N/A')
        
        # Add request context if available
        if hasattr(record, 'method'):
            log_record['method'] = record.method
        if hasattr(record, 'path'):
            log_record['path'] = record.path
        if hasattr(record, 'status_code'):
            log_record['status_code'] = record.status_code
        if hasattr(record, 'latency_ms'):
            log_record['latency_ms'] = record.latency_ms
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        
        # Add error information if available
        if record.exc_info:
            log_record['error_stack'] = self.formatException(record.exc_info)
        
        # Mask PII in the message and other string fields
        for key, value in log_record.items():
            if isinstance(value, str):
                log_record[key] = self.pii_masker.mask(value)


def configure_structlog() -> None:
    """Configure structlog for structured logging"""
    
    # Configure structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
    ]
    
    # Add JSON processor for production
    if os.getenv('ENVIRONMENT', 'development') != 'development':
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            int(os.getenv('LOG_LEVEL_NUM', logging.INFO))
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def setup_logging() -> None:
    """Setup logging configuration for the entire application"""
    
    # Get log level from environment
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Configure structlog first
    configure_structlog()
    
    # Logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': CustomJSONFormatter,
                'format': '%(timestamp)s %(level)s %(service)s %(env)s %(version)s %(logger)s %(request_id)s %(message)s'
            },
            'simple': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'filters': {
            'correlation': {
                '()': CorrelationFilter,
            }
        },
        'handlers': {
            'stdout': {
                'class': 'logging.StreamHandler',
                'stream': sys.stdout,
                'formatter': 'json' if os.getenv('ENVIRONMENT', 'development') != 'development' else 'simple',
                'filters': ['correlation'],
                'level': log_level,
            }
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['stdout'],
                'level': log_level,
                'propagate': False,
            },
            'uvicorn.access': {
                'handlers': ['stdout'],
                'level': log_level,
                'propagate': False,
            },
            'uvicorn.error': {
                'handlers': ['stdout'],
                'level': log_level,
                'propagate': False,
            },
            'uvicorn': {
                'handlers': ['stdout'],
                'level': log_level,
                'propagate': False,
            },
            'fastapi': {
                'handlers': ['stdout'],
                'level': log_level,
                'propagate': False,
            },
            'sqlalchemy.engine': {
                'handlers': ['stdout'],
                'level': 'WARNING',  # Reduce noise from SQL queries
                'propagate': False,
            }
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Set root logger level
    logging.getLogger().setLevel(getattr(logging, log_level))


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a configured logger instance"""
    return structlog.get_logger(name)


# Global logger instance for the module
logger = get_logger(__name__)
