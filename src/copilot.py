"""
Linux Agentic Copilot - Main Application
Integrates all modules and provides unified API
"""

import logging
import asyncio
from pathlib import Path
from typing import Optional

from .core.event_loop import EventLoop, Event, EventPriority
from .core.security import SecurityManager
from .core.plugin_api import PluginManager, CoreAPI

from .modules.logging.logger import LoggerManager, LogLevel
from .modules.input.keyboard import KeyboardController, HotkeyManager
from .modules.input.mouse import MouseController
from .modules.input.macros import MacroEngine
from .modules.window.manager import WindowManager
from .modules.screenshot.capture import ScreenshotCapture, ScreenRecorder


class LinuxCopilot:
    """
    Linux Agentic Copilot - Main Application Class

    Features:
    - Event-driven architecture
    - Modular plugin system
    - Cross-platform support (X11/Wayland)
    - Comprehensive automation capabilities
    - Security and permission management
    """

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        plugin_dir: Optional[Path] = None,
        config_dir: Optional[Path] = None
    ):
        """
        Initialize the Linux Copilot

        Args:
            log_dir: Directory for log files
            plugin_dir: Directory containing plugins
            config_dir: Directory for configuration files
        """
        # Setup paths
        self.config_dir = config_dir or Path.home() / ".config" / "linux-copilot"
        self.log_dir = log_dir or Path.home() / ".local" / "share" / "linux-copilot" / "logs"
        self.plugin_dir = plugin_dir or self.config_dir / "plugins"

        # Create directories
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.plugin_dir.mkdir(parents=True, exist_ok=True)

        # Initialize logging
        self.logger_manager = LoggerManager(
            log_dir=self.log_dir,
            console_level=LogLevel.INFO,
            file_level=LogLevel.DEBUG,
            enable_syslog=False
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Linux Agentic Copilot")

        # Initialize core systems
        self.event_loop = EventLoop()
        self.security = SecurityManager()

        # Initialize modules
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        self.macro_engine = MacroEngine(self.keyboard, self.mouse)
        self.hotkey_manager = HotkeyManager()
        self.window_manager = WindowManager()
        self.screenshot = ScreenshotCapture()
        self.recorder = ScreenRecorder()

        # Module registry for plugins
        self._module_registry = {
            'keyboard': self.keyboard,
            'mouse': self.mouse,
            'macros': self.macro_engine,
            'hotkeys': self.hotkey_manager,
            'windows': self.window_manager,
            'screenshot': self.screenshot,
            'recorder': self.recorder,
            'logger': self.logger_manager,
            'security': self.security
        }

        # Initialize plugin system
        self.core_api = CoreAPI(
            self.event_loop,
            self.security,
            self._module_registry
        )
        self.plugin_manager = PluginManager(self.core_api)

        self._running = False
        self._initialized = False

    async def initialize(self):
        """Initialize the copilot and all subsystems"""
        if self._initialized:
            self.logger.warning("Already initialized")
            return

        self.logger.info("Initializing subsystems...")

        # Start event loop
        await self.event_loop.start()

        # Setup event handlers
        self._setup_event_handlers()

        # Load plugins from plugin directory
        plugin_count = self.plugin_manager.load_plugins_from_directory(self.plugin_dir)
        self.logger.info(f"Loaded {plugin_count} plugins")

        # Initialize all loaded plugins
        for plugin_name in self.plugin_manager.list_plugins():
            await self.plugin_manager.initialize_plugin(plugin_name)

        self._initialized = True
        self.logger.info("Linux Copilot initialized successfully")

    def _setup_event_handlers(self):
        """Setup core event handlers"""
        # Subscribe to system events
        self.event_loop.subscribe("window_changed", self._on_window_changed)
        self.event_loop.subscribe("hotkey_pressed", self._on_hotkey_pressed)
        self.event_loop.subscribe("macro_replay", self._on_macro_replay)

    async def _on_window_changed(self, event: Event):
        """Handle window change events"""
        self.logger.debug(f"Window changed: {event.data}")

    async def _on_hotkey_pressed(self, event: Event):
        """Handle hotkey events"""
        self.logger.info(f"Hotkey pressed: {event.data.get('hotkey')}")

    async def _on_macro_replay(self, event: Event):
        """Handle macro replay events"""
        macro_name = event.data.get('macro_name')
        await self.macro_engine.replay_macro(macro_name)

    async def start(self):
        """Start the copilot"""
        if not self._initialized:
            await self.initialize()

        self._running = True
        self.logger.info("Linux Copilot started")

        # Emit startup event
        self.event_loop.emit(Event(
            event_type="system_started",
            data={},
            priority=EventPriority.HIGH
        ))

    async def stop(self):
        """Stop the copilot gracefully"""
        self.logger.info("Stopping Linux Copilot...")
        self._running = False

        # Emit shutdown event
        self.event_loop.emit(Event(
            event_type="system_stopping",
            data={},
            priority=EventPriority.CRITICAL
        ))

        # Unload all plugins
        for plugin_name in self.plugin_manager.list_plugins():
            await self.plugin_manager.unload_plugin(plugin_name)

        # Stop subsystems
        await self.event_loop.stop()

        self.logger.info("Linux Copilot stopped")

    async def run(self):
        """Run the copilot until stopped"""
        await self.start()

        try:
            await self.event_loop.run_forever()
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        finally:
            await self.stop()

    def get_module(self, module_name: str):
        """
        Get a module by name

        Args:
            module_name: Name of module

        Returns:
            Module instance or None
        """
        return self._module_registry.get(module_name)

    def emit_event(self, event_type: str, data: dict, priority: EventPriority = EventPriority.NORMAL):
        """
        Emit a custom event

        Args:
            event_type: Type of event
            data: Event data
            priority: Event priority
        """
        self.event_loop.emit(Event(
            event_type=event_type,
            data=data,
            priority=priority
        ))


async def main():
    """Main entry point"""
    copilot = LinuxCopilot()
    await copilot.run()


if __name__ == "__main__":
    asyncio.run(main())
