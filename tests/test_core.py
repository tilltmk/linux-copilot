"""
Tests for core modules (EventLoop, Security, PluginAPI)
"""

import pytest
import asyncio
from pathlib import Path

from src.core.event_loop import EventLoop, Event, EventPriority
from src.core.security import SecurityManager, PermissionLevel, SecurityContext
from src.core.plugin_api import PluginManager, CoreAPI


class TestEventLoop:
    """Test EventLoop functionality"""

    @pytest.mark.asyncio
    async def test_event_loop_start_stop(self):
        """Test starting and stopping event loop"""
        loop = EventLoop()
        await loop.start()
        assert loop._running is True
        await loop.stop()
        assert loop._running is False

    @pytest.mark.asyncio
    async def test_event_subscription(self):
        """Test event subscription and emission"""
        loop = EventLoop()
        await loop.start()

        received_events = []

        async def handler(event):
            received_events.append(event)

        loop.subscribe("test_event", handler)

        # Emit test event
        test_event = Event(
            event_type="test_event",
            data={"message": "test"},
            priority=EventPriority.NORMAL
        )
        loop.emit(test_event)

        # Wait for processing
        await asyncio.sleep(0.5)

        assert len(received_events) == 1
        assert received_events[0].event_type == "test_event"
        assert received_events[0].data["message"] == "test"

        await loop.stop()

    @pytest.mark.asyncio
    async def test_event_unsubscription(self):
        """Test event unsubscription"""
        loop = EventLoop()
        await loop.start()

        received_events = []

        async def handler(event):
            received_events.append(event)

        loop.subscribe("test_event", handler)
        loop.unsubscribe("test_event", handler)

        # Emit test event
        test_event = Event(event_type="test_event", data={})
        loop.emit(test_event)

        # Wait for processing
        await asyncio.sleep(0.5)

        # Should not have received event
        assert len(received_events) == 0

        await loop.stop()


class TestSecurityManager:
    """Test SecurityManager functionality"""

    def test_security_context(self):
        """Test security context creation"""
        context = SecurityContext.current()
        assert context.user is not None
        assert context.uid >= 0
        assert context.gid >= 0

    def test_permission_checking(self):
        """Test permission checking"""
        security = SecurityManager()

        # User level should be allowed by default
        assert security.check_permission("test_operation", PermissionLevel.USER) is True

        # Dangerous should be denied by default
        assert security.check_permission("dangerous_op", PermissionLevel.DANGEROUS) is False

    def test_whitelist_operation(self):
        """Test operation whitelisting"""
        security = SecurityManager()

        # Initially denied
        assert security.check_permission("dangerous_op", PermissionLevel.DANGEROUS) is False

        # Whitelist it
        security.whitelist_operation("dangerous_op")

        # Now allowed
        assert security.check_permission("dangerous_op", PermissionLevel.DANGEROUS) is True

    def test_blacklist_operation(self):
        """Test operation blacklisting"""
        security = SecurityManager()

        # Initially allowed
        assert security.check_permission("test_op", PermissionLevel.USER) is True

        # Blacklist it
        security.blacklist_operation("test_op")

        # Now denied
        assert security.check_permission("test_op", PermissionLevel.USER) is False

    def test_input_sanitization(self):
        """Test input sanitization"""
        security = SecurityManager()

        # Test dangerous characters removal
        dangerous_input = "test`command`|dangerous"
        sanitized = security.sanitize_input(dangerous_input)

        assert "`" not in sanitized
        assert "|" not in sanitized
        assert "test" in sanitized

    def test_path_validation(self):
        """Test path validation"""
        security = SecurityManager()

        # Valid path
        assert security.validate_path("/home/user/test.txt") is True

        # Path traversal attempt
        assert security.validate_path("/home/user/../etc/passwd") is False

        # Null byte injection
        assert security.validate_path("/home/user/test\0.txt") is False


class TestPluginManager:
    """Test PluginManager functionality"""

    def test_plugin_manager_creation(self):
        """Test plugin manager creation"""
        event_loop = EventLoop()
        security = SecurityManager()
        core_api = CoreAPI(event_loop, security, {})

        plugin_manager = PluginManager(core_api)
        assert plugin_manager is not None
        assert len(plugin_manager.list_plugins()) == 0

    def test_list_plugins(self):
        """Test listing plugins"""
        event_loop = EventLoop()
        security = SecurityManager()
        core_api = CoreAPI(event_loop, security, {})

        plugin_manager = PluginManager(core_api)
        plugins = plugin_manager.list_plugins()

        assert isinstance(plugins, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
