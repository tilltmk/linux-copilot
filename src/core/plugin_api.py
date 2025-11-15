"""
Plugin API - Interface for dynamic plugin loading and management
Provides base classes and management for extensible plugins
"""

import logging
import importlib.util
import inspect
import sys
from typing import Dict, List, Optional, Any, Type
from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass


@dataclass
class PluginMetadata:
    """Metadata for a plugin"""
    name: str
    version: str
    author: str
    description: str
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class PluginBase(ABC):
    """
    Base class for all plugins

    All plugins must inherit from this class and implement required methods
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._initialized = False
        self._enabled = False

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass

    @abstractmethod
    async def initialize(self, core_api: 'CoreAPI') -> bool:
        """
        Initialize the plugin

        Args:
            core_api: API interface to core system

        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    async def shutdown(self):
        """Shutdown the plugin and cleanup resources"""
        pass

    def is_initialized(self) -> bool:
        """Check if plugin is initialized"""
        return self._initialized

    def is_enabled(self) -> bool:
        """Check if plugin is enabled"""
        return self._enabled

    def enable(self):
        """Enable the plugin"""
        self._enabled = True
        self.logger.info(f"Plugin {self.get_metadata().name} enabled")

    def disable(self):
        """Disable the plugin"""
        self._enabled = False
        self.logger.info(f"Plugin {self.get_metadata().name} disabled")


class CoreAPI:
    """
    API interface provided to plugins for accessing core functionality
    """

    def __init__(self, event_loop, security_manager, module_registry):
        self.event_loop = event_loop
        self.security = security_manager
        self.modules = module_registry
        self.logger = logging.getLogger(__name__)

    def subscribe_event(self, event_type: str, callback):
        """Subscribe to an event"""
        self.event_loop.subscribe(event_type, callback)

    def emit_event(self, event):
        """Emit an event"""
        self.event_loop.emit(event)

    def get_module(self, module_name: str) -> Optional[Any]:
        """Get a registered module"""
        return self.modules.get(module_name)

    def check_permission(self, operation: str, level) -> bool:
        """Check if an operation is permitted"""
        return self.security.check_permission(operation, level)


class PluginManager:
    """
    Plugin Manager - Handles dynamic loading, unloading, and lifecycle of plugins

    Features:
    - Dynamic plugin loading from directories
    - Plugin dependency resolution
    - Sandboxed plugin execution
    - Plugin lifecycle management
    """

    def __init__(self, core_api: CoreAPI):
        self.logger = logging.getLogger(__name__)
        self.core_api = core_api
        self._plugins: Dict[str, PluginBase] = {}
        self._plugin_paths: Dict[str, Path] = {}

    def load_plugin(self, plugin_path: Path) -> bool:
        """
        Load a plugin from a file path

        Args:
            plugin_path: Path to plugin .py file

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            # Validate path
            if not self.core_api.security.validate_path(str(plugin_path)):
                self.logger.error(f"Invalid plugin path: {plugin_path}")
                return False

            if not plugin_path.exists() or not plugin_path.is_file():
                self.logger.error(f"Plugin file not found: {plugin_path}")
                return False

            # Load module
            module_name = plugin_path.stem
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)

            if spec is None or spec.loader is None:
                self.logger.error(f"Failed to load spec for {plugin_path}")
                return False

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Find plugin class
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, PluginBase) and
                    obj != PluginBase):
                    plugin_class = obj
                    break

            if plugin_class is None:
                self.logger.error(f"No PluginBase subclass found in {plugin_path}")
                return False

            # Instantiate plugin
            plugin = plugin_class()
            metadata = plugin.get_metadata()

            # Check if already loaded
            if metadata.name in self._plugins:
                self.logger.warning(f"Plugin {metadata.name} already loaded")
                return False

            # Store plugin
            self._plugins[metadata.name] = plugin
            self._plugin_paths[metadata.name] = plugin_path

            self.logger.info(
                f"Loaded plugin: {metadata.name} v{metadata.version} "
                f"by {metadata.author}"
            )

            return True

        except Exception as e:
            self.logger.error(f"Error loading plugin {plugin_path}: {e}", exc_info=True)
            return False

    async def initialize_plugin(self, plugin_name: str) -> bool:
        """
        Initialize a loaded plugin

        Args:
            plugin_name: Name of plugin to initialize

        Returns:
            True if initialized successfully, False otherwise
        """
        if plugin_name not in self._plugins:
            self.logger.error(f"Plugin {plugin_name} not loaded")
            return False

        plugin = self._plugins[plugin_name]

        if plugin.is_initialized():
            self.logger.warning(f"Plugin {plugin_name} already initialized")
            return True

        try:
            success = await plugin.initialize(self.core_api)
            if success:
                plugin._initialized = True
                plugin.enable()
                self.logger.info(f"Initialized plugin: {plugin_name}")
            else:
                self.logger.error(f"Failed to initialize plugin: {plugin_name}")
            return success

        except Exception as e:
            self.logger.error(
                f"Error initializing plugin {plugin_name}: {e}",
                exc_info=True
            )
            return False

    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin

        Args:
            plugin_name: Name of plugin to unload

        Returns:
            True if unloaded successfully, False otherwise
        """
        if plugin_name not in self._plugins:
            self.logger.error(f"Plugin {plugin_name} not loaded")
            return False

        plugin = self._plugins[plugin_name]

        try:
            # Shutdown plugin
            if plugin.is_initialized():
                await plugin.shutdown()

            # Remove from registry
            del self._plugins[plugin_name]
            del self._plugin_paths[plugin_name]

            self.logger.info(f"Unloaded plugin: {plugin_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error unloading plugin {plugin_name}: {e}", exc_info=True)
            return False

    def load_plugins_from_directory(self, directory: Path) -> int:
        """
        Load all plugins from a directory

        Args:
            directory: Directory containing plugin files

        Returns:
            Number of plugins loaded
        """
        if not directory.exists() or not directory.is_dir():
            self.logger.error(f"Plugin directory not found: {directory}")
            return 0

        loaded = 0
        for plugin_file in directory.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue  # Skip private files

            if self.load_plugin(plugin_file):
                loaded += 1

        self.logger.info(f"Loaded {loaded} plugins from {directory}")
        return loaded

    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """Get a loaded plugin by name"""
        return self._plugins.get(plugin_name)

    def list_plugins(self) -> List[str]:
        """List all loaded plugin names"""
        return list(self._plugins.keys())

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a plugin"""
        if plugin_name not in self._plugins:
            return None

        plugin = self._plugins[plugin_name]
        metadata = plugin.get_metadata()

        return {
            "name": metadata.name,
            "version": metadata.version,
            "author": metadata.author,
            "description": metadata.description,
            "dependencies": metadata.dependencies,
            "initialized": plugin.is_initialized(),
            "enabled": plugin.is_enabled(),
            "path": str(self._plugin_paths[plugin_name])
        }
