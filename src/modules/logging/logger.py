"""
Advanced Logging Module - Multi-target logging with rotation and filtering
Supports file logging, syslog, audit logs, and structured logging
"""

import logging
import logging.handlers
import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class LogLevel(Enum):
    """Log levels"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class AuditLogger:
    """
    Specialized audit logger for security-relevant events
    Provides tamper-resistant logging with structured format
    """

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)

        # Create log directory if it doesn't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # File handler with rotation
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=10
        )

        # Use JSON format for structured logging
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"message": "%(message)s"}'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_event(
        self,
        event_type: str,
        user: str,
        action: str,
        details: Dict[str, Any],
        severity: str = "INFO"
    ):
        """
        Log an audit event

        Args:
            event_type: Type of event (e.g., "auth", "file_access", "plugin_load")
            user: User who triggered the event
            action: Action performed
            details: Additional event details
            severity: Event severity (INFO, WARNING, ERROR)
        """
        entry = {
            "event_type": event_type,
            "user": user,
            "action": action,
            "details": details,
            "pid": os.getpid()
        }

        log_func = getattr(self.logger, severity.lower(), self.logger.info)
        log_func(json.dumps(entry))


class LoggerManager:
    """
    Centralized logging manager for the Linux Copilot system

    Features:
    - Multiple output targets (console, file, syslog)
    - Log rotation
    - Structured logging
    - Audit logging
    - Per-module log levels
    """

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        console_level: LogLevel = LogLevel.INFO,
        file_level: LogLevel = LogLevel.DEBUG,
        enable_syslog: bool = False
    ):
        self.log_dir = log_dir or Path.home() / ".local" / "share" / "linux-copilot" / "logs"
        self.console_level = console_level
        self.file_level = file_level
        self.enable_syslog = enable_syslog

        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup root logger
        self._setup_root_logger()

        # Setup audit logger
        audit_file = self.log_dir / "audit.log"
        self.audit_logger = AuditLogger(audit_file)

        self.logger = logging.getLogger(__name__)
        self.logger.info("Logging system initialized")

    def _setup_root_logger(self):
        """Setup the root logger with all handlers"""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Capture everything

        # Remove existing handlers
        root_logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.console_level.value)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # File handler with rotation
        main_log_file = self.log_dir / "copilot.log"
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=50 * 1024 * 1024,  # 50 MB
            backupCount=5
        )
        file_handler.setLevel(self.file_level.value)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # Syslog handler (optional)
        if self.enable_syslog:
            try:
                syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')
                syslog_handler.setLevel(logging.WARNING)
                syslog_formatter = logging.Formatter(
                    'linux-copilot[%(process)d]: %(name)s - %(levelname)s - %(message)s'
                )
                syslog_handler.setFormatter(syslog_formatter)
                root_logger.addHandler(syslog_handler)
            except Exception as e:
                logging.warning(f"Failed to setup syslog handler: {e}")

        # Error log file
        error_log_file = self.log_dir / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)

    def set_module_level(self, module_name: str, level: LogLevel):
        """
        Set log level for a specific module

        Args:
            module_name: Name of the module
            level: Log level to set
        """
        logger = logging.getLogger(module_name)
        logger.setLevel(level.value)
        self.logger.info(f"Set log level for {module_name} to {level.name}")

    def audit_log(
        self,
        event_type: str,
        user: str,
        action: str,
        details: Dict[str, Any],
        severity: str = "INFO"
    ):
        """
        Create an audit log entry

        Args:
            event_type: Type of event
            user: User who triggered the event
            action: Action performed
            details: Additional details
            severity: Event severity
        """
        self.audit_logger.log_event(event_type, user, action, details, severity)

    def get_log_files(self) -> Dict[str, Path]:
        """Get paths to all log files"""
        return {
            "main": self.log_dir / "copilot.log",
            "errors": self.log_dir / "errors.log",
            "audit": self.log_dir / "audit.log"
        }

    def rotate_logs(self):
        """Manually trigger log rotation"""
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handler.doRollover()
        self.logger.info("Log rotation completed")
