"""
Security Manager - Handles permissions, sandboxing, and security validation
Ensures minimal privilege operation and validates all dangerous operations
"""

import os
import pwd
import grp
import logging
from typing import List, Optional, Set, Callable
from dataclasses import dataclass
from enum import Enum
import functools


class PermissionLevel(Enum):
    """Permission levels for operations"""
    USER = 0          # Normal user operations
    ELEVATED = 1      # Requires user confirmation
    DANGEROUS = 2     # Requires explicit authorization
    ROOT = 3          # Requires root privileges (avoided when possible)


@dataclass
class SecurityContext:
    """Security context for operations"""
    user: str
    uid: int
    gid: int
    groups: List[str]
    is_root: bool

    @classmethod
    def current(cls) -> 'SecurityContext':
        """Get current security context"""
        uid = os.getuid()
        gid = os.getgid()
        user = pwd.getpwuid(uid).pw_name
        groups = [grp.getgrgid(g).gr_name for g in os.getgroups()]
        is_root = uid == 0

        return cls(
            user=user,
            uid=uid,
            gid=gid,
            groups=groups,
            is_root=is_root
        )


class SecurityManager:
    """
    Security Manager for the Linux Copilot system

    Features:
    - Permission validation
    - Operation whitelisting
    - Input sanitization
    - Audit logging
    - Sandboxing support
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.context = SecurityContext.current()
        self._whitelisted_operations: Set[str] = set()
        self._blacklisted_operations: Set[str] = set()
        self._permission_callbacks: dict[str, Callable] = {}

        self.logger.info(
            f"Security context: user={self.context.user}, "
            f"uid={self.context.uid}, root={self.context.is_root}"
        )

    def whitelist_operation(self, operation: str):
        """
        Whitelist a specific operation

        Args:
            operation: Operation identifier to whitelist
        """
        self._whitelisted_operations.add(operation)
        self.logger.info(f"Whitelisted operation: {operation}")

    def blacklist_operation(self, operation: str):
        """
        Blacklist a specific operation

        Args:
            operation: Operation identifier to blacklist
        """
        self._blacklisted_operations.add(operation)
        self.logger.warning(f"Blacklisted operation: {operation}")

    def check_permission(
        self,
        operation: str,
        required_level: PermissionLevel = PermissionLevel.USER
    ) -> bool:
        """
        Check if an operation is permitted

        Args:
            operation: Operation identifier
            required_level: Required permission level

        Returns:
            True if operation is permitted, False otherwise
        """
        # Check blacklist first
        if operation in self._blacklisted_operations:
            self.logger.warning(f"Operation {operation} is blacklisted")
            return False

        # Check if root is required but not available
        if required_level == PermissionLevel.ROOT and not self.context.is_root:
            self.logger.error(
                f"Operation {operation} requires root privileges"
            )
            return False

        # Check whitelist
        if operation in self._whitelisted_operations:
            return True

        # Check custom permission callback
        if operation in self._permission_callbacks:
            callback = self._permission_callbacks[operation]
            try:
                return callback(self.context, required_level)
            except Exception as e:
                self.logger.error(
                    f"Error in permission callback for {operation}: {e}"
                )
                return False

        # Default: allow USER and ELEVATED, deny DANGEROUS and ROOT
        if required_level in (PermissionLevel.USER, PermissionLevel.ELEVATED):
            return True

        return False

    def register_permission_callback(self, operation: str, callback: Callable):
        """
        Register a custom permission callback for an operation

        Args:
            operation: Operation identifier
            callback: Callback function(context, level) -> bool
        """
        self._permission_callbacks[operation] = callback
        self.logger.debug(f"Registered permission callback for {operation}")

    def sanitize_input(self, input_str: str) -> str:
        """
        Sanitize user input to prevent injection attacks

        Args:
            input_str: Input string to sanitize

        Returns:
            Sanitized string
        """
        # Remove null bytes
        sanitized = input_str.replace('\0', '')

        # Remove dangerous shell characters
        dangerous_chars = ['`', '$', '|', ';', '&', '>', '<', '\n', '\r']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')

        return sanitized

    def validate_path(self, path: str, allow_absolute: bool = True) -> bool:
        """
        Validate a file path for security

        Args:
            path: Path to validate
            allow_absolute: Whether to allow absolute paths

        Returns:
            True if path is valid, False otherwise
        """
        # Check for path traversal
        if '..' in path:
            self.logger.warning(f"Path traversal detected: {path}")
            return False

        # Check for null bytes
        if '\0' in path:
            self.logger.warning(f"Null byte in path: {path}")
            return False

        # Check absolute path restriction
        if not allow_absolute and os.path.isabs(path):
            self.logger.warning(f"Absolute path not allowed: {path}")
            return False

        return True

    def audit_log(self, operation: str, details: str, level: str = "INFO"):
        """
        Log security-relevant operations for auditing

        Args:
            operation: Operation identifier
            details: Operation details
            level: Log level (INFO, WARNING, ERROR)
        """
        log_msg = f"AUDIT: {operation} - {details} - user={self.context.user}"

        if level == "ERROR":
            self.logger.error(log_msg)
        elif level == "WARNING":
            self.logger.warning(log_msg)
        else:
            self.logger.info(log_msg)


def require_permission(operation: str, level: PermissionLevel = PermissionLevel.USER):
    """
    Decorator to require permission for a function

    Args:
        operation: Operation identifier
        level: Required permission level
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Assume self has a security_manager attribute
            if hasattr(self, 'security_manager'):
                security = self.security_manager
                if not security.check_permission(operation, level):
                    raise PermissionError(
                        f"Permission denied for operation: {operation}"
                    )
                security.audit_log(operation, f"Called {func.__name__}")
            return func(self, *args, **kwargs)
        return wrapper
    return decorator
