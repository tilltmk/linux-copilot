"""
Example Plugin: Screenshot Tool
Demonstrates screenshot and recording capabilities
"""

from pathlib import Path
from src.core.plugin_api import PluginBase, PluginMetadata
from src.core.event_loop import Event, EventPriority


class ScreenshotToolPlugin(PluginBase):
    """
    Example plugin for screenshot and recording automation

    Features:
    - Hotkey-triggered screenshots
    - Scheduled screenshots
    - Auto-recording on specific events
    """

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="screenshot_tool",
            version="1.0.0",
            author="Linux Copilot",
            description="Automated screenshot and recording tool",
            dependencies=[]
        )

    async def initialize(self, core_api) -> bool:
        """Initialize the plugin"""
        try:
            self.core_api = core_api
            self.screenshot = core_api.get_module('screenshot')
            self.recorder = core_api.get_module('recorder')

            if not self.screenshot or not self.recorder:
                self.logger.error("Screenshot/Recorder modules not available")
                return False

            # Subscribe to events
            core_api.subscribe_event("take_screenshot", self._take_screenshot)
            core_api.subscribe_event("start_recording", self._start_recording)
            core_api.subscribe_event("stop_recording", self._stop_recording)

            # Setup save directory
            self.save_dir = Path.home() / "Screenshots"
            self.save_dir.mkdir(parents=True, exist_ok=True)

            self.logger.info("Screenshot Tool Plugin initialized")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            return False

    async def shutdown(self):
        """Shutdown the plugin"""
        # Stop recording if active
        if self.recorder.is_recording():
            await self.recorder.stop_recording()

        self.logger.info("Screenshot Tool Plugin shutting down")

    async def _take_screenshot(self, event):
        """Take a screenshot"""
        try:
            mode = event.data.get('mode', 'fullscreen')
            output_path = self.save_dir / f"screenshot_{mode}.png"

            if mode == 'fullscreen':
                path = await self.screenshot.capture_fullscreen(output_path)
            elif mode == 'window':
                window_id = event.data.get('window_id')
                path = await self.screenshot.capture_window(window_id, output_path)
            elif mode == 'interactive':
                path = await self.screenshot.capture_interactive(output_path)
            else:
                self.logger.warning(f"Unknown screenshot mode: {mode}")
                return

            self.logger.info(f"Screenshot saved to {path}")

            # Emit completion event
            self.core_api.emit_event(Event(
                event_type="screenshot_completed",
                data={'path': str(path)},
                priority=EventPriority.NORMAL
            ))

        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")

    async def _start_recording(self, event):
        """Start screen recording"""
        try:
            fps = event.data.get('fps', 30)
            audio = event.data.get('audio', False)

            path = await self.recorder.start_recording(fps=fps, audio=audio)
            self.logger.info(f"Recording started, will save to {path}")

        except Exception as e:
            self.logger.error(f"Error starting recording: {e}")

    async def _stop_recording(self, event):
        """Stop screen recording"""
        try:
            path = await self.recorder.stop_recording()
            if path:
                self.logger.info(f"Recording saved to {path}")

                # Emit completion event
                self.core_api.emit_event(Event(
                    event_type="recording_completed",
                    data={'path': str(path)},
                    priority=EventPriority.NORMAL
                ))

        except Exception as e:
            self.logger.error(f"Error stopping recording: {e}")
