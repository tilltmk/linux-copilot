"""
Screenshot and Screen Recording Module
Cross-platform support for X11 and Wayland
"""

import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from enum import Enum


class CaptureMode(Enum):
    """Screenshot capture modes"""
    FULLSCREEN = "fullscreen"
    WINDOW = "window"
    REGION = "region"


class ScreenshotCapture:
    """
    Screenshot capture for X11 and Wayland

    Features:
    - Fullscreen capture
    - Window capture
    - Region capture
    - Multiple format support (PNG, JPG)
    - Clipboard integration
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._detect_backend()
        self._detect_tools()

    def _detect_backend(self):
        """Detect if running under X11 or Wayland"""
        session_type = subprocess.getoutput("echo $XDG_SESSION_TYPE").strip()
        self.backend = session_type if session_type in ['x11', 'wayland'] else 'x11'
        self.logger.info(f"Detected screenshot backend: {self.backend}")

    def _detect_tools(self):
        """Detect available screenshot tools"""
        self.tools = {}

        # Check for scrot (X11)
        if subprocess.call(["which", "scrot"], stdout=subprocess.DEVNULL) == 0:
            self.tools['scrot'] = True

        # Check for maim (X11)
        if subprocess.call(["which", "maim"], stdout=subprocess.DEVNULL) == 0:
            self.tools['maim'] = True

        # Check for grim (Wayland)
        if subprocess.call(["which", "grim"], stdout=subprocess.DEVNULL) == 0:
            self.tools['grim'] = True

        # Check for slurp (Wayland region selection)
        if subprocess.call(["which", "slurp"], stdout=subprocess.DEVNULL) == 0:
            self.tools['slurp'] = True

        # Check for ImageMagick import
        if subprocess.call(["which", "import"], stdout=subprocess.DEVNULL) == 0:
            self.tools['import'] = True

        self.logger.info(f"Available screenshot tools: {list(self.tools.keys())}")

    async def capture_fullscreen(
        self,
        output_path: Optional[Path] = None,
        format: str = "png"
    ) -> Path:
        """
        Capture fullscreen screenshot

        Args:
            output_path: Path to save screenshot (auto-generated if None)
            format: Image format (png, jpg)

        Returns:
            Path to saved screenshot
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path.home() / f"screenshot_{timestamp}.{format}"

        try:
            if self.backend == 'wayland' and 'grim' in self.tools:
                # Use grim for Wayland
                proc = await asyncio.create_subprocess_exec(
                    "grim", str(output_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            elif 'maim' in self.tools:
                # Use maim for X11 (preferred)
                proc = await asyncio.create_subprocess_exec(
                    "maim", str(output_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            elif 'scrot' in self.tools:
                # Use scrot for X11
                proc = await asyncio.create_subprocess_exec(
                    "scrot", str(output_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            elif 'import' in self.tools:
                # Use ImageMagick as fallback
                proc = await asyncio.create_subprocess_exec(
                    "import", "-window", "root", str(output_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            else:
                raise RuntimeError("No screenshot tool available")

            self.logger.info(f"Captured fullscreen screenshot to {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Error capturing screenshot: {e}")
            raise

    async def capture_window(
        self,
        window_id: Optional[str] = None,
        output_path: Optional[Path] = None,
        format: str = "png"
    ) -> Path:
        """
        Capture screenshot of a specific window

        Args:
            window_id: Window ID (None for active window)
            output_path: Path to save screenshot
            format: Image format

        Returns:
            Path to saved screenshot
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path.home() / f"window_{timestamp}.{format}"

        try:
            if self.backend == 'x11' and 'maim' in self.tools:
                if window_id:
                    # Capture specific window
                    proc = await asyncio.create_subprocess_exec(
                        "maim", "-i", window_id, str(output_path),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                else:
                    # Capture active window
                    proc = await asyncio.create_subprocess_exec(
                        "maim", "-i", "$(xdotool getactivewindow)", str(output_path),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        shell=True
                    )
                await proc.wait()

            elif self.backend == 'wayland' and 'grim' in self.tools:
                # For Wayland, capture focused window using slurp
                if 'slurp' in self.tools:
                    # Get window geometry with slurp
                    proc = await asyncio.create_subprocess_exec(
                        "sh", "-c",
                        f"grim -g \"$(slurp)\" {output_path}",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await proc.wait()
                else:
                    self.logger.warning("Window capture on Wayland requires slurp")
                    return await self.capture_fullscreen(output_path, format)

            else:
                raise RuntimeError("No suitable tool for window capture")

            self.logger.info(f"Captured window screenshot to {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Error capturing window: {e}")
            raise

    async def capture_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        output_path: Optional[Path] = None,
        format: str = "png"
    ) -> Path:
        """
        Capture screenshot of a specific region

        Args:
            x: X coordinate of top-left corner
            y: Y coordinate of top-left corner
            width: Region width
            height: Region height
            output_path: Path to save screenshot
            format: Image format

        Returns:
            Path to saved screenshot
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path.home() / f"region_{timestamp}.{format}"

        try:
            if self.backend == 'wayland' and 'grim' in self.tools:
                # Use grim with geometry for Wayland
                geometry = f"{x},{y} {width}x{height}"
                proc = await asyncio.create_subprocess_exec(
                    "grim", "-g", geometry, str(output_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            elif 'maim' in self.tools:
                # Use maim with geometry for X11
                proc = await asyncio.create_subprocess_exec(
                    "maim", "-g", f"{width}x{height}+{x}+{y}", str(output_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            elif 'import' in self.tools:
                # Use ImageMagick
                proc = await asyncio.create_subprocess_exec(
                    "import", "-window", "root",
                    "-crop", f"{width}x{height}+{x}+{y}",
                    str(output_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            else:
                raise RuntimeError("No suitable tool for region capture")

            self.logger.info(f"Captured region screenshot to {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Error capturing region: {e}")
            raise

    async def capture_interactive(
        self,
        output_path: Optional[Path] = None,
        format: str = "png"
    ) -> Path:
        """
        Interactive screenshot selection (user selects region)

        Args:
            output_path: Path to save screenshot
            format: Image format

        Returns:
            Path to saved screenshot
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path.home() / f"screenshot_{timestamp}.{format}"

        try:
            if self.backend == 'wayland' and 'grim' in self.tools and 'slurp' in self.tools:
                # Use grim + slurp for Wayland
                proc = await asyncio.create_subprocess_exec(
                    "sh", "-c",
                    f"grim -g \"$(slurp)\" {output_path}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            elif 'maim' in self.tools:
                # Use maim with selection for X11
                proc = await asyncio.create_subprocess_exec(
                    "maim", "-s", str(output_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            else:
                raise RuntimeError("No suitable tool for interactive capture")

            self.logger.info(f"Captured interactive screenshot to {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Error in interactive capture: {e}")
            raise


class ScreenRecorder:
    """
    Screen recorder for X11 and Wayland

    Features:
    - Fullscreen recording
    - Window recording
    - Region recording
    - Audio support
    - Multiple format support
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._detect_backend()
        self._recording_process: Optional[asyncio.subprocess.Process] = None
        self._recording = False

    def _detect_backend(self):
        """Detect if running under X11 or Wayland"""
        session_type = subprocess.getoutput("echo $XDG_SESSION_TYPE").strip()
        self.backend = session_type if session_type in ['x11', 'wayland'] else 'x11'
        self.logger.info(f"Detected recording backend: {self.backend}")

    async def start_recording(
        self,
        output_path: Optional[Path] = None,
        fps: int = 30,
        audio: bool = False
    ) -> Path:
        """
        Start screen recording

        Args:
            output_path: Path to save recording
            fps: Frames per second
            audio: Include audio

        Returns:
            Path where recording will be saved
        """
        if self._recording:
            raise RuntimeError("Already recording")

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path.home() / f"recording_{timestamp}.mp4"

        try:
            if self.backend == 'wayland':
                # Use wf-recorder for Wayland
                cmd = ["wf-recorder", "-f", str(output_path), "-r", str(fps)]
                if audio:
                    cmd.extend(["-a"])

            else:
                # Use ffmpeg for X11
                display = subprocess.getoutput("echo $DISPLAY").strip()
                cmd = [
                    "ffmpeg", "-video_size", "1920x1080",
                    "-framerate", str(fps),
                    "-f", "x11grab",
                    "-i", display,
                ]
                if audio:
                    cmd.extend(["-f", "pulse", "-i", "default"])
                cmd.extend(["-c:v", "libx264", "-preset", "ultrafast", str(output_path)])

            self._recording_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            self._recording = True
            self._output_path = output_path

            self.logger.info(f"Started recording to {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Error starting recording: {e}")
            raise

    async def stop_recording(self) -> Optional[Path]:
        """
        Stop screen recording

        Returns:
            Path to saved recording
        """
        if not self._recording or not self._recording_process:
            self.logger.warning("Not currently recording")
            return None

        try:
            # Send interrupt signal
            self._recording_process.terminate()
            await self._recording_process.wait()

            self._recording = False
            output_path = self._output_path
            self._recording_process = None

            self.logger.info(f"Stopped recording, saved to {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Error stopping recording: {e}")
            return None

    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self._recording
