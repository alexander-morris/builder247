import logging
import logging.handlers
import os
import re
from pathlib import Path
from threading import Lock
from typing import Optional, Dict, Any
from datetime import datetime

class SecureLogger:
    """Thread-safe secure logging with rotation and injection prevention."""
    
    def __init__(self, log_dir: str = "logs", max_bytes: int = 10485760, backup_count: int = 5):
        """Initialize the secure logger.
        
        Args:
            log_dir: Directory to store log files
            max_bytes: Maximum size of each log file before rotation (default: 10MB)
            backup_count: Number of backup files to keep (default: 5)
        """
        self.log_dir = Path(log_dir)
        self._lock = Lock()
        self._loggers: Dict[str, logging.Logger] = {}
        
        # Ensure log directory exists with proper permissions
        os.makedirs(self.log_dir, mode=0o750, exist_ok=True)
        # Explicitly set permissions in case umask interferes
        os.chmod(self.log_dir, 0o750)
        
        # Set up the main logger
        self.setup_logger('main', 'main.log', max_bytes, backup_count)
        
        # Set up security logger for security-related events
        self.setup_logger('security', 'security.log', max_bytes, backup_count)
        
        # Set up file operations logger
        self.setup_logger('file_ops', 'file_operations.log', max_bytes, backup_count)
    
    def setup_logger(self, name: str, filename: str, max_bytes: int, backup_count: int) -> None:
        """Set up a new logger with the specified configuration."""
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        
        # Remove any existing handlers
        logger.handlers = []
        
        # Create a rotating file handler
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            mode='a',
            encoding='utf-8'
        )
        
        # Create a secure formatter that escapes special characters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        self._loggers[name] = logger
    
    def _sanitize_message(self, message: str) -> str:
        """Sanitize log messages to prevent log injection."""
        # Replace control characters with spaces
        message = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', ' ', message)
        
        # Replace newlines and carriage returns with spaces
        message = message.replace('\n', ' ').replace('\r', ' ')
        
        # Remove any timestamp-like patterns that could be used for injection
        message = re.sub(r'\d{4}[-/]\d{2}[-/]\d{2}(?:\s+\d{2}:\d{2}:\d{2})?', '[TIMESTAMP]', message)
        
        # Remove log level patterns
        message = re.sub(r'\b(INFO|WARNING|ERROR|DEBUG|CRITICAL)\b', '[LEVEL]', message)
        
        # Remove logger name patterns
        message = re.sub(r'\s+-\s+\w+\s+-\s+', ' ', message)
        
        # Normalize multiple spaces to single space
        message = re.sub(r'\s+', ' ', message)
        
        # Remove any remaining control characters
        message = ''.join(char for char in message if ord(char) >= 32 or char == ' ')
        
        # Escape any remaining special characters
        message = re.sub(r'[^\w\s\-_.,!?@#$%^&*()[\]{}|;:\'\"<>\/\\+=]', '', message)
        
        return message.strip()
    
    def _format_extra(self, extra: Optional[Dict[str, Any]] = None) -> str:
        """Format extra fields for logging."""
        if not extra:
            return ''
        
        # Sanitize and format extra fields
        fields = []
        for key, value in extra.items():
            safe_key = self._sanitize_message(str(key))
            safe_value = self._sanitize_message(str(value))
            if safe_key and safe_value:  # Only add non-empty fields
                fields.append(f"{safe_key}={safe_value}")
        
        return ' - ' + ', '.join(fields) if fields else ''
    
    def log(self, level: str, message: str, logger_name: str = 'main', extra: Optional[Dict[str, Any]] = None) -> None:
        """Thread-safe logging with sanitization."""
        with self._lock:
            logger = self._loggers.get(logger_name)
            if not logger:
                return
            
            try:
                # Sanitize the message and format extra fields
                safe_message = self._sanitize_message(message)
                extra_str = self._format_extra(extra)
                
                # Get the logging level
                log_level = getattr(logging, level.upper(), logging.INFO)
                
                # Log the message
                logger.log(log_level, f"{safe_message}{extra_str}")
                
            except Exception as e:
                # If there's an error during logging, try to log it to the main logger
                try:
                    main_logger = self._loggers.get('main')
                    if main_logger:
                        main_logger.error(f"Error during logging: {str(e)}")
                except:
                    pass  # If even this fails, we can't do much more
    
    def info(self, message: str, logger_name: str = 'main', extra: Optional[Dict[str, Any]] = None) -> None:
        """Log an info message."""
        self.log('INFO', message, logger_name, extra)
    
    def warning(self, message: str, logger_name: str = 'main', extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a warning message."""
        self.log('WARNING', message, logger_name, extra)
    
    def error(self, message: str, logger_name: str = 'main', extra: Optional[Dict[str, Any]] = None) -> None:
        """Log an error message."""
        self.log('ERROR', message, logger_name, extra)
    
    def security(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a security-related message."""
        self.log('INFO', message, 'security', extra)
    
    def file_operation(self, operation: str, path: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a file operation."""
        extra = extra or {}
        extra.update({
            'operation': operation,
            'path': str(path),
            'timestamp': datetime.utcnow().isoformat()
        })
        self.log('INFO', f"File operation: {operation}", 'file_ops', extra) 