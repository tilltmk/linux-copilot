"""
Window Manager - Cross-platform window management for X11 and Wayland
Handles window enumeration, manipulation, and monitoring
"""

import logging
import asyncio
import subprocess
import re
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class WindowState(Enum):
    """Window states"""
    NORMAL = "normal"
    MAXIMIZED = "maximized"
    MINIMIZED = "minimized"
    FULLSCREEN = "fullscreen"
    HIDDEN = "hidden"


@dataclass
class WindowInfo:
    """Information about a window"""
    window_id: str
    title: str
    wm_class: str
    pid: int
    x: int
    y: int
    width: int
    height: int
    desktop: int
    state: WindowState
    is_active: bool

    def __str__(self):
        return (
            f"Window(id={self.window_id}, title='{self.title}', "
            f"class={self.wm_class}, pos=({self.x},{self.y}), "
            f"size={self.width}x{self.height})"
        )


class WindowManager:
    """
    Cross-platform window manager for X11 and Wayland

    Features:
    - List all windows
    - Get active window
    - Activate/focus windows
    - Move and resize windows
    - Minimize/maximize/close windows
    - Virtual desktop management
    - Window monitoring
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._detect_backend()

    def _detect_backend(self):
        """Detect if running under X11 or Wayland"""
        session_type = subprocess.getoutput("echo $XDG_SESSION_TYPE").strip()
        self.backend = session_type if session_type in ['x11', 'wayland'] else 'x11'
        self.logger.info(f"Detected window backend: {self.backend}")

    async def get_all_windows(self) -> List[WindowInfo]:
        """
        Get information about all windows

        Returns:
            List of WindowInfo objects
        """
        if self.backend == 'x11':
            return await self._get_windows_x11()
        else:
            return await self._get_windows_wayland()

    async def _get_windows_x11(self) -> List[WindowInfo]:
        """Get windows using wmctrl (X11)"""
        windows = []

        try:
            # Run wmctrl to list windows
            proc = await asyncio.create_subprocess_exec(
                "wmctrl", "-l", "-G", "-p", "-x",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            # Parse output
            for line in stdout.decode().strip().split('\n'):
                if not line:
                    continue

                parts = line.split(None, 9)
                if len(parts) < 10:
                    continue

                window_id = parts[0]
                desktop = int(parts[1])
                pid = int(parts[2])
                x = int(parts[3])
                y = int(parts[4])
                width = int(parts[5])
                height = int(parts[6])
                wm_class = parts[7]
                title = parts[9]

                window_info = WindowInfo(
                    window_id=window_id,
                    title=title,
                    wm_class=wm_class,
                    pid=pid,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    desktop=desktop,
                    state=WindowState.NORMAL,
                    is_active=False
                )

                windows.append(window_info)

            # Get active window
            active_id = await self._get_active_window_id_x11()
            for window in windows:
                if window.window_id == active_id:
                    window.is_active = True
                    break

        except Exception as e:
            self.logger.error(f"Error getting X11 windows: {e}")

        return windows

    async def _get_windows_wayland(self) -> List[WindowInfo]:
        """Get windows on Wayland (limited functionality)"""
        windows = []

        try:
            # Try using swaymsg for Sway compositor
            proc = await asyncio.create_subprocess_exec(
                "swaymsg", "-t", "get_tree",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                # Parse Sway window tree
                import json
                tree = json.loads(stdout.decode())
                windows = self._parse_sway_tree(tree)
            else:
                self.logger.warning("Wayland window listing requires compositor support")

        except FileNotFoundError:
            self.logger.warning("swaymsg not found - Wayland window listing unavailable")
        except Exception as e:
            self.logger.error(f"Error getting Wayland windows: {e}")

        return windows

    def _parse_sway_tree(self, node: Dict, windows: List[WindowInfo] = None) -> List[WindowInfo]:
        """Parse Sway window tree recursively"""
        if windows is None:
            windows = []

        if node.get("type") == "con" and node.get("name"):
            rect = node.get("rect", {})
            window_info = WindowInfo(
                window_id=str(node.get("id", 0)),
                title=node.get("name", ""),
                wm_class=node.get("app_id", "unknown"),
                pid=node.get("pid", 0),
                x=rect.get("x", 0),
                y=rect.get("y", 0),
                width=rect.get("width", 0),
                height=rect.get("height", 0),
                desktop=0,
                state=WindowState.NORMAL,
                is_active=node.get("focused", False)
            )
            windows.append(window_info)

        # Recurse into children
        for child in node.get("nodes", []):
            self._parse_sway_tree(child, windows)

        for child in node.get("floating_nodes", []):
            self._parse_sway_tree(child, windows)

        return windows

    async def _get_active_window_id_x11(self) -> str:
        """Get active window ID (X11)"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "xdotool", "getactivewindow",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            return stdout.decode().strip()
        except Exception:
            return ""

    async def get_active_window(self) -> Optional[WindowInfo]:
        """
        Get the currently active window

        Returns:
            WindowInfo of active window or None
        """
        windows = await self.get_all_windows()
        for window in windows:
            if window.is_active:
                return window
        return None

    async def activate_window(self, window_id: str):
        """
        Activate (focus) a window

        Args:
            window_id: Window identifier
        """
        try:
            if self.backend == 'x11':
                proc = await asyncio.create_subprocess_exec(
                    "wmctrl", "-i", "-a", window_id,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()
            else:
                # Sway: focus window
                proc = await asyncio.create_subprocess_exec(
                    "swaymsg", f"[con_id={window_id}]", "focus",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            self.logger.debug(f"Activated window {window_id}")

        except Exception as e:
            self.logger.error(f"Error activating window: {e}")

    async def close_window(self, window_id: str):
        """
        Close a window

        Args:
            window_id: Window identifier
        """
        try:
            if self.backend == 'x11':
                proc = await asyncio.create_subprocess_exec(
                    "wmctrl", "-i", "-c", window_id,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()
            else:
                proc = await asyncio.create_subprocess_exec(
                    "swaymsg", f"[con_id={window_id}]", "kill",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            self.logger.info(f"Closed window {window_id}")

        except Exception as e:
            self.logger.error(f"Error closing window: {e}")

    async def move_window(self, window_id: str, x: int, y: int):
        """
        Move a window to specific position

        Args:
            window_id: Window identifier
            x: X coordinate
            y: Y coordinate
        """
        try:
            if self.backend == 'x11':
                proc = await asyncio.create_subprocess_exec(
                    "wmctrl", "-i", "-r", window_id, "-e", f"0,{x},{y},-1,-1",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()
            else:
                proc = await asyncio.create_subprocess_exec(
                    "swaymsg", f"[con_id={window_id}]", "move", "position", str(x), str(y),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            self.logger.debug(f"Moved window {window_id} to ({x}, {y})")

        except Exception as e:
            self.logger.error(f"Error moving window: {e}")

    async def resize_window(self, window_id: str, width: int, height: int):
        """
        Resize a window

        Args:
            window_id: Window identifier
            width: New width
            height: New height
        """
        try:
            if self.backend == 'x11':
                proc = await asyncio.create_subprocess_exec(
                    "wmctrl", "-i", "-r", window_id, "-e", f"0,-1,-1,{width},{height}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()
            else:
                proc = await asyncio.create_subprocess_exec(
                    "swaymsg", f"[con_id={window_id}]", "resize", "set",
                    str(width), str(height),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            self.logger.debug(f"Resized window {window_id} to {width}x{height}")

        except Exception as e:
            self.logger.error(f"Error resizing window: {e}")

    async def maximize_window(self, window_id: str):
        """Maximize a window"""
        try:
            if self.backend == 'x11':
                proc = await asyncio.create_subprocess_exec(
                    "wmctrl", "-i", "-r", window_id, "-b", "add,maximized_vert,maximized_horz",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()
            else:
                proc = await asyncio.create_subprocess_exec(
                    "swaymsg", f"[con_id={window_id}]", "fullscreen", "enable",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            self.logger.debug(f"Maximized window {window_id}")

        except Exception as e:
            self.logger.error(f"Error maximizing window: {e}")

    async def minimize_window(self, window_id: str):
        """Minimize a window"""
        try:
            if self.backend == 'x11':
                proc = await asyncio.create_subprocess_exec(
                    "xdotool", "windowminimize", window_id,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()
            else:
                self.logger.warning("Minimize not fully supported on Wayland")

            self.logger.debug(f"Minimized window {window_id}")

        except Exception as e:
            self.logger.error(f"Error minimizing window: {e}")

    async def get_window_by_title(self, title_pattern: str) -> Optional[WindowInfo]:
        """
        Find a window by title pattern

        Args:
            title_pattern: Regex pattern to match window title

        Returns:
            WindowInfo or None if not found
        """
        windows = await self.get_all_windows()
        pattern = re.compile(title_pattern, re.IGNORECASE)

        for window in windows:
            if pattern.search(window.title):
                return window

        return None

    async def get_window_by_class(self, wm_class: str) -> Optional[WindowInfo]:
        """
        Find a window by WM_CLASS

        Args:
            wm_class: Window class to match

        Returns:
            WindowInfo or None if not found
        """
        windows = await self.get_all_windows()

        for window in windows:
            if wm_class.lower() in window.wm_class.lower():
                return window

        return None
