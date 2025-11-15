"""
Mouse Input Module - Monitor and control mouse events
Supports X11 and Wayland (with limitations)
"""

import logging
import asyncio
import subprocess
from typing import Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class MouseButton(Enum):
    """Mouse buttons"""
    LEFT = 1
    MIDDLE = 2
    RIGHT = 3
    SCROLL_UP = 4
    SCROLL_DOWN = 5


@dataclass
class MouseEvent:
    """Mouse event data"""
    x: int
    y: int
    button: Optional[MouseButton]
    pressed: bool  # True for press, False for release
    timestamp: float


class MouseController:
    """
    Mouse controller for monitoring and simulating mouse input

    Features:
    - Mouse movement
    - Click simulation
    - Scroll simulation
    - Position tracking
    - Works with both X11 and Wayland
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._detect_backend()

    def _detect_backend(self):
        """Detect if running under X11 or Wayland"""
        session_type = subprocess.getoutput("echo $XDG_SESSION_TYPE").strip()
        self.backend = session_type if session_type in ['x11', 'wayland'] else 'x11'
        self.logger.info(f"Detected backend: {self.backend}")

    async def get_position(self) -> Tuple[int, int]:
        """
        Get current mouse position

        Returns:
            Tuple of (x, y) coordinates
        """
        try:
            if self.backend == 'x11':
                # Use xdotool to get mouse position
                proc = await asyncio.create_subprocess_exec(
                    "xdotool", "getmouselocation", "--shell",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await proc.communicate()

                # Parse output
                lines = stdout.decode().strip().split('\n')
                x = y = 0
                for line in lines:
                    if line.startswith('X='):
                        x = int(line.split('=')[1])
                    elif line.startswith('Y='):
                        y = int(line.split('=')[1])

                return x, y
            else:
                # Wayland doesn't allow querying mouse position easily
                self.logger.warning("Getting mouse position on Wayland is restricted")
                return 0, 0

        except Exception as e:
            self.logger.error(f"Error getting mouse position: {e}")
            return 0, 0

    async def move(self, x: int, y: int, relative: bool = False):
        """
        Move mouse to position

        Args:
            x: X coordinate
            y: Y coordinate
            relative: If True, move relative to current position
        """
        try:
            if self.backend == 'x11':
                if relative:
                    cmd = ["xdotool", "mousemove_relative", "--", str(x), str(y)]
                else:
                    cmd = ["xdotool", "mousemove", str(x), str(y)]

                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            else:
                # Use ydotool for Wayland
                if relative:
                    cmd = ["ydotool", "mousemove", "--", str(x), str(y)]
                else:
                    cmd = ["ydotool", "mousemove", "-a", str(x), str(y)]

                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            self.logger.debug(f"Moved mouse to ({x}, {y})")

        except Exception as e:
            self.logger.error(f"Error moving mouse: {e}")

    async def click(self, button: MouseButton = MouseButton.LEFT, clicks: int = 1):
        """
        Simulate mouse click

        Args:
            button: Mouse button to click
            clicks: Number of clicks (1 for single, 2 for double)
        """
        try:
            if self.backend == 'x11':
                cmd = ["xdotool", "click", "--repeat", str(clicks), str(button.value)]
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            else:
                # Use ydotool for Wayland
                for _ in range(clicks):
                    # Mouse down
                    cmd_down = ["ydotool", "click", f"0x4{button.value - 1}"]
                    proc = await asyncio.create_subprocess_exec(
                        *cmd_down,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await proc.wait()

            self.logger.debug(f"Clicked {button.name} button {clicks} times")

        except Exception as e:
            self.logger.error(f"Error clicking mouse: {e}")

    async def scroll(self, amount: int):
        """
        Simulate mouse scroll

        Args:
            amount: Scroll amount (positive for up, negative for down)
        """
        try:
            if self.backend == 'x11':
                button = MouseButton.SCROLL_UP if amount > 0 else MouseButton.SCROLL_DOWN
                repeats = abs(amount)

                cmd = ["xdotool", "click", "--repeat", str(repeats), str(button.value)]
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            else:
                # Use ydotool for Wayland
                cmd = ["ydotool", "click", f"0x{amount:02x}"]
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

            self.logger.debug(f"Scrolled {amount}")

        except Exception as e:
            self.logger.error(f"Error scrolling: {e}")

    async def drag(self, from_x: int, from_y: int, to_x: int, to_y: int):
        """
        Simulate mouse drag

        Args:
            from_x: Starting X coordinate
            from_y: Starting Y coordinate
            to_x: Ending X coordinate
            to_y: Ending Y coordinate
        """
        try:
            # Move to starting position
            await self.move(from_x, from_y)

            # Mouse down
            if self.backend == 'x11':
                proc = await asyncio.create_subprocess_exec(
                    "xdotool", "mousedown", "1",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()

                # Move to end position
                await self.move(to_x, to_y)

                # Mouse up
                proc = await asyncio.create_subprocess_exec(
                    "xdotool", "mouseup", "1",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()
            else:
                # Simplified Wayland drag
                self.logger.warning("Drag on Wayland requires ydotool configuration")

            self.logger.debug(f"Dragged from ({from_x}, {from_y}) to ({to_x}, {to_y})")

        except Exception as e:
            self.logger.error(f"Error dragging mouse: {e}")
