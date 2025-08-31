"""
Unit tests for logging configuration
"""
import json
import logging
import os
from unittest.mock import patch, Mock
import pytest
import structlog

from app.infrastructure.logging.config import (
    setup_logging, get_logger, CorrelationFilter, CustomJSONFormatter
)


class TestCorrelationFilter:
    """Test cases for correlation filter"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.filter = CorrelationFilter()
    
    def test_filter_adds_correlation_id_from_record(self):
        """Test that filter adds correlation ID from record attribute"""
        record = Mock()
        record.correlation_id = "test-correlation-id"
        
        result = self.filter.filter(record)
        
        assert result is True
        assert record.correlation_id == "test-correlation-id"
    
    def test_filter_adds_default_when_no_correlation_id(self):
        """Test that filter adds default when no correlation ID"""
        record = Mock()
        del record.correlation_id  # Remove attribute
        
        with patch('structlog.get_context', return_value={}):
            result = self.filter.filter(record)
        
        assert result is True
        assert record.correlation_id == "N/A"
    
    def test_filter_gets_correlation_id_from_structlog_context(self):
        """Test that filter gets correlation ID from structlog context"""
        record = Mock()
        del record.correlation_id  # Remove attribute
        
        with patch('structlog.get_context', return_value={'request_id': 'structlog-id'}):
            result = self.filter.filter(record)
        
        assert result is True
        assert record.correlation_id == "structlog-id"


class TestCustomJSONFormatter:
    """Test cases for custom JSON formatter"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.formatter = CustomJSONFormatter()
    
    @patch.dict(os.environ, {
        'SERVICE_NAME': 'test-service',
        'ENVIRONMENT': 'test',
        'VERSION': '1.0.0'
    })
    def test_add_fields_includes_standard_fields(self):
        """Test that standard fields are added to log record"""
        log_record = {}
        record = Mock()
        record.levelname = "INFO"
        record.name = "test.logger"
        record.correlation_id = "test-id"
        record.exc_info = None
        
        self.formatter.add_fields(log_record, record, {})
        
        # Check standard fields
        assert log_record['level'] == "INFO"
        assert log_record['service'] == "test-service"
        assert log_record['env'] == "test"
        assert log_record['version'] == "1.0.0"
        assert log_record['logger'] == "test.logger"
        assert log_record['request_id'] == "test-id"
        assert 'timestamp' in log_record
    
    def test_add_fields_includes_request_context(self):
        """Test that request context fields are added when available"""
        log_record = {}
        record = Mock()
        record.levelname = "INFO"
        record.name = "test.logger"
        record.correlation_id = "test-id"
        record.exc_info = None
        record.method = "GET"
        record.path = "/api/test"
        record.status_code = 200
        record.latency_ms = 100.5
        record.user_id = "user123"
        
        self.formatter.add_fields(log_record, record, {})
        
        # Check request context fields
        assert log_record['method'] == "GET"
        assert log_record['path'] == "/api/test"
        assert log_record['status_code'] == 200
        assert log_record['latency_ms'] == 100.5
        assert log_record['user_id'] == "user123"
    
    def test_add_fields_includes_error_stack(self):
        """Test that error stack is added when exception info is available"""
        log_record = {}
        record = Mock()
        record.levelname = "ERROR"
        record.name = "test.logger"
        record.correlation_id = "test-id"
        record.exc_info = (Exception, Exception("test error"), None)
        
        with patch.object(self.formatter, 'formatException', return_value='test stack trace'):
            self.formatter.add_fields(log_record, record, {})
        
        assert log_record['error_stack'] == 'test stack trace'
    
    def test_add_fields_masks_pii(self):
        """Test that PII is masked in string fields"""
        log_record = {'message': 'Contact user@example.com'}
        record = Mock()
        record.levelname = "INFO"
        record.name = "test.logger"
        record.correlation_id = "test-id"
        record.exc_info = None
        
        self.formatter.add_fields(log_record, record, {})
        
        # Check that email is masked
        assert 'us***@example.com' in log_record['message']


class TestLoggingSetup:
    """Test cases for logging setup"""
    
    @patch.dict(os.environ, {'LOG_LEVEL': 'DEBUG'})
    @patch('app.infrastructure.logging.config.configure_structlog')
    @patch('logging.config.dictConfig')
    def test_setup_logging_configures_with_debug_level(self, mock_dict_config, mock_structlog):
        """Test that logging is setup with DEBUG level from environment"""
        setup_logging()
        
        # Check that structlog was configured
        mock_structlog.assert_called_once()
        
        # Check that logging config was called
        mock_dict_config.assert_called_once()
        
        # Check that the config contains DEBUG level
        config = mock_dict_config.call_args[0][0]
        assert config['handlers']['stdout']['level'] == 'DEBUG'
        assert config['loggers']['']['level'] == 'DEBUG'
    
    @patch.dict(os.environ, {'ENVIRONMENT': 'production'})
    @patch('app.infrastructure.logging.config.configure_structlog')
    @patch('logging.config.dictConfig')
    def test_setup_logging_uses_json_formatter_in_production(self, mock_dict_config, mock_structlog):
        """Test that JSON formatter is used in production environment"""
        setup_logging()
        
        config = mock_dict_config.call_args[0][0]
        assert config['handlers']['stdout']['formatter'] == 'json'
    
    @patch.dict(os.environ, {'ENVIRONMENT': 'development'})
    @patch('app.infrastructure.logging.config.configure_structlog')
    @patch('logging.config.dictConfig')
    def test_setup_logging_uses_simple_formatter_in_development(self, mock_dict_config, mock_structlog):
        """Test that simple formatter is used in development environment"""
        setup_logging()
        
        config = mock_dict_config.call_args[0][0]
        assert config['handlers']['stdout']['formatter'] == 'simple'
    
    def test_get_logger_returns_structlog_logger(self):
        """Test that get_logger returns a structlog bound logger"""
        logger = get_logger("test")
        
        assert isinstance(logger, structlog.BoundLogger) or hasattr(logger, 'info')


class TestJSONLogging:
    """Integration tests for JSON logging output"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.formatter = CustomJSONFormatter()
    
    def test_json_log_format_is_valid(self):
        """Test that logged output is valid JSON"""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.correlation_id = "test-id"
        
        formatted = self.formatter.format(record)
        
        # Should be valid JSON
        try:
            parsed = json.loads(formatted)
            assert isinstance(parsed, dict)
            assert 'message' in parsed
            assert 'timestamp' in parsed
            assert 'level' in parsed
            assert 'request_id' in parsed
        except json.JSONDecodeError:
            pytest.fail("Formatted log is not valid JSON")
    
    def test_json_log_contains_required_fields(self):
        """Test that JSON log contains all required fields"""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py", 
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.correlation_id = "test-id"
        
        formatted = self.formatter.format(record)
        parsed = json.loads(formatted)
        
        required_fields = [
            'timestamp', 'level', 'service', 'env', 'version',
            'logger', 'request_id', 'message'
        ]
        
        for field in required_fields:
            assert field in parsed, f"Required field '{field}' missing from log"
