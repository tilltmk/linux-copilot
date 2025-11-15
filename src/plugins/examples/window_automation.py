"""
Example Plugin: Window Automation
Demonstrates window management automation capabilities
"""

import logging
from src.core.plugin_api import PluginBase, PluginMetadata


class WindowAutomationPlugin(PluginBase):
    """
    Example plugin that automates window management tasks

    Features:
    - Auto-arrange windows in grid layout
    - Focus window by application name
    - Minimize inactive windows
    """

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="window_automation",
            version="1.0.0",
            author="Linux Copilot",
            description="Automates window management tasks",
            dependencies=[]
        )

    async def initialize(self, core_api) -> bool:
        """Initialize the plugin"""
        try:
            self.core_api = core_api
            self.window_manager = core_api.get_module('windows')

            if not self.window_manager:
                self.logger.error("Window manager module not available")
                return False

            # Subscribe to events
            core_api.subscribe_event("arrange_windows", self._arrange_windows)
            core_api.subscribe_event("focus_app", self._focus_app)

            self.logger.info("Window Automation Plugin initialized")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            return False

    async def shutdown(self):
        """Shutdown the plugin"""
        self.logger.info("Window Automation Plugin shutting down")

    async def _arrange_windows(self, event):
        """Arrange windows in a grid layout"""
        try:
            windows = await self.window_manager.get_all_windows()

            # Simple 2x2 grid layout
            screen_width = 1920  # Could be detected dynamically
            screen_height = 1080

            window_width = screen_width // 2
            window_height = screen_height // 2

            positions = [
                (0, 0),
                (window_width, 0),
                (0, window_height),
                (window_width, window_height)
            ]

            for i, window in enumerate(windows[:4]):  # Arrange first 4 windows
                x, y = positions[i]
                await self.window_manager.move_window(window.window_id, x, y)
                await self.window_manager.resize_window(
                    window.window_id,
                    window_width,
                    window_height
                )

            self.logger.info(f"Arranged {min(len(windows), 4)} windows in grid")

        except Exception as e:
            self.logger.error(f"Error arranging windows: {e}")

    async def _focus_app(self, event):
        """Focus window by application name"""
        try:
            app_name = event.data.get('app_name')
            if not app_name:
                return

            window = await self.window_manager.get_window_by_class(app_name)
            if window:
                await self.window_manager.activate_window(window.window_id)
                self.logger.info(f"Focused window: {window.title}")
            else:
                self.logger.warning(f"Window not found for app: {app_name}")

        except Exception as e:
            self.logger.error(f"Error focusing app: {e}")
