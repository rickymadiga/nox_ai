"""
Centralized Logging Service
Handles all application logging with file and console output
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Any
from datetime import datetime
import json

# ============================================================================
# CONFIGURATION
# ============================================================================

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# ============================================================================
# APP LOGGER
# ============================================================================

class AppLogger:
    """Centralized logging service with file and console output."""
    
    # Class-level logger cache
    _loggers = {}
    
    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        log_file: Optional[str] = None,
        enable_console: bool = True,
        enable_file: bool = True
    ):
        """
        Initialize logger.
        
        Args:
            name: Logger name (usually __name__)
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Custom log file name (optional)
            enable_console: Enable console output
            enable_file: Enable file output
        """
        self.name = name
        self.level = level
        self.logger = self._get_or_create_logger(name, level)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Set level
        self.logger.setLevel(level)
        
        # Add handlers
        if enable_file:
            self._add_file_handler(log_file, level)
        
        if enable_console:
            self._add_console_handler(level)
    
    @staticmethod
    def _get_or_create_logger(name: str, level: int) -> logging.Logger:
        """Get or create logger instance."""
        if name not in AppLogger._loggers:
            logger = logging.getLogger(name)
            AppLogger._loggers[name] = logger
        return AppLogger._loggers[name]
    
    def _add_file_handler(self, log_file: Optional[str], level: int):
        """Add file handler to logger."""
        try:
            # Determine log file name
            if log_file:
                log_path = LOG_DIR / log_file
            else:
                # Use module name or date-based filename
                date_str = datetime.now().strftime('%Y%m%d')
                module_name = self.name.split('.')[-1]
                log_path = LOG_DIR / f"app_{date_str}.log"
            
            # Create file handler
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(level)
            
            # Create formatter
            formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            self.logger.addHandler(file_handler)
        
        except Exception as e:
            print(f"Failed to add file handler: {e}")
    
    def _add_console_handler(self, level: int):
        """Add console handler to logger."""
        try:
            # Create console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            
            # Create formatter
            formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
            console_handler.setFormatter(formatter)
            
            # Add handler to logger
            self.logger.addHandler(console_handler)
        
        except Exception as e:
            print(f"Failed to add console handler: {e}")
    
    # ========================================================================
    # LOGGING METHODS
    # ========================================================================
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def warn(self, message: str, **kwargs):
        """Alias for warning."""
        self.warning(message, **kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message."""
        self.logger.error(message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Log critical message."""
        self.logger.critical(message, exc_info=exc_info, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception."""
        self.logger.exception(message, **kwargs)
    
    # ========================================================================
    # CONVENIENCE METHODS
    # ========================================================================
    
    def log_function_call(self, func_name: str, args: dict = None):
        """Log function call with arguments."""
        args_str = json.dumps(args) if args else "{}"
        self.debug(f"Function called: {func_name} with args: {args_str}")
    
    def log_function_result(self, func_name: str, result: Any, duration: float = 0):
        """Log function result."""
        result_str = str(result)[:100]  # Truncate for readability
        if duration:
            self.debug(f"Function completed: {func_name} in {duration:.3f}s - Result: {result_str}")
        else:
            self.debug(f"Function completed: {func_name} - Result: {result_str}")
    
    def log_error_with_context(
        self,
        message: str,
        error: Exception,
        context: dict = None
    ):
        """Log error with context information."""
        error_msg = f"{message}\nError: {str(error)}"
        if context:
            error_msg += f"\nContext: {json.dumps(context, default=str)}"
        self.error(error_msg, exc_info=True)
    
    def log_performance(
        self,
        operation: str,
        duration: float,
        threshold: float = 1.0,
        metadata: dict = None
    ):
        """Log performance metric."""
        level_msg = ""
        if duration > threshold * 2:
            level = self.logger.warning
            level_msg = "⚠️ SLOW"
        elif duration > threshold:
            level = self.logger.info
            level_msg = "ℹ️ NORMAL"
        else:
            level = self.logger.debug
            level_msg = "✓ FAST"
        
        msg = f"{level_msg} Performance: {operation} took {duration:.3f}s"
        if metadata:
            msg += f" - {json.dumps(metadata, default=str)}"
        
        level(msg)


# ============================================================================
# STRUCTURED LOGGING
# ============================================================================

class StructuredLogger:
    """Structured logging for complex data."""
    
    def __init__(self, name: str):
        """Initialize structured logger."""
        self.logger = AppLogger(name)
    
    def log_event(
        self,
        event_type: str,
        severity: str = "INFO",
        data: dict = None,
        **kwargs
    ):
        """Log structured event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "data": data or {},
            **kwargs
        }
        
        log_message = json.dumps(event)
        
        if severity == "DEBUG":
            self.logger.debug(log_message)
        elif severity == "INFO":
            self.logger.info(log_message)
        elif severity == "WARNING":
            self.logger.warning(log_message)
        elif severity == "ERROR":
            self.logger.error(log_message)
        elif severity == "CRITICAL":
            self.logger.critical(log_message)
    
    def log_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: int = None,
        duration: float = None,
        error: str = None
    ):
        """Log API call."""
        self.log_event(
            event_type="api_call",
            severity="INFO" if not error else "ERROR",
            data={
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration": duration,
                "error": error
            }
        )
    
    def log_database_operation(
        self,
        operation: str,
        table: str,
        rows_affected: int = None,
        duration: float = None,
        error: str = None
    ):
        """Log database operation."""
        self.log_event(
            event_type="database_operation",
            severity="INFO" if not error else "ERROR",
            data={
                "operation": operation,
                "table": table,
                "rows_affected": rows_affected,
                "duration": duration,
                "error": error
            }
        )
    
    def log_user_action(
        self,
        action: str,
        username: str,
        status: str = "success",
        details: dict = None
    ):
        """Log user action."""
        self.log_event(
            event_type="user_action",
            severity="INFO" if status == "success" else "WARNING",
            data={
                "action": action,
                "username": username,
                "status": status,
                "details": details or {}
            }
        )
    
    def log_authentication(
        self,
        username: str,
        action: str,
        success: bool,
        error: str = None
    ):
        """Log authentication event."""
        self.log_event(
            event_type="authentication",
            severity="INFO" if success else "WARNING",
            data={
                "username": username,
                "action": action,
                "success": success,
                "error": error
            }
        )


# ============================================================================
# LOG MANAGEMENT
# ============================================================================

class LogManager:
    """Manage application logs."""
    
    @staticmethod
    def get_log_files() -> list:
        """Get all log files."""
        if not LOG_DIR.exists():
            return []
        return sorted(LOG_DIR.glob("*.log"))
    
    @staticmethod
    def get_latest_log() -> Optional[Path]:
        """Get latest log file."""
        log_files = LogManager.get_log_files()
        return log_files[-1] if log_files else None
    
    @staticmethod
    def read_log_file(filename: str, tail: int = 100) -> list:
        """Read log file (optionally tail last N lines)."""
        log_path = LOG_DIR / filename
        
        if not log_path.exists():
            return []
        
        try:
            with open(log_path, 'r') as f:
                lines = f.readlines()
            
            return lines[-tail:] if tail else lines
        
        except Exception as e:
            print(f"Failed to read log file: {e}")
            return []
    
    @staticmethod
    def clear_old_logs(days: int = 7):
        """Clear log files older than specified days."""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        
        for log_file in LOG_DIR.glob("*.log"):
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff:
                    log_file.unlink()
            except Exception as e:
                print(f"Failed to delete log file {log_file}: {e}")
    
    @staticmethod
    def get_log_stats() -> dict:
        """Get log file statistics."""
        log_files = LogManager.get_log_files()
        
        total_size = sum(f.stat().st_size for f in log_files)
        
        return {
            "total_files": len(log_files),
            "total_size_mb": total_size / (1024 * 1024),
            "latest_log": str(log_files[-1].name) if log_files else None,
            "oldest_log": str(log_files[0].name) if log_files else None
        }


# ============================================================================
# MODULE-LEVEL CONVENIENCE
# ============================================================================

# Global logger instance
_default_logger = None

def get_logger(name: str, level: int = logging.INFO) -> AppLogger:
    """Get a logger instance."""
    return AppLogger(name, level)

def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)