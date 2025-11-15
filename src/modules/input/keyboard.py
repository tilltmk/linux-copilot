"""
Keyboard Input Module - Monitor and control keyboard events
Supports X11 and Wayland (with limitations)
"""

import logging
import asyncio
from typing import Callable, Optional, Dict, Set, List
from dataclasses import dataclass
from enum import Enum
import subprocess


class KeyModifier(Enum):
    """Keyboard modifiers"""
    CTRL = "ctrl"
    ALT = "alt"
    SHIFT = "shift"
    SUPER = "super"  # Windows/Meta key


@dataclass
class KeyEvent:
    """Keyboard event data"""
    key: str
    modifiers: Set[KeyModifier]
    pressed: bool  # True for press, False for release
    timestamp: float

    def __str__(self):
        mods = "+".join(m.value for m in self.modifiers)
        action = "pressed" if self.pressed else "released"
        return f"{mods}+{self.key} {action}" if mods else f"{self.key} {action}"


class KeyboardController:
    """
    Keyboard controller for monitoring and simulating keyboard input

    Features:
    - Key press/release simulation
    - Text typing
    - Key combination support
    - Works with both X11 and Wayland (via different backends)
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._detect_backend()

    def _detect_backend(self):
        """Detect if running under X11 or Wayland"""
        session_type = subprocess.getoutput("echo $XDG_SESSION_TYPE").strip()
        self.backend = session_type if session_type in ['x11', 'wayland'] else 'x11'
        self.logger.info(f"Detected backend: {self.backend}")

    async def press_key(self, key: str, modifiers: Optional[Set[KeyModifier]] = None):
        """
        Press a key (with optional modifiers)

        Args:
            key: Key to press (e.g., 'a', 'Return', 'Escape')
            modifiers: Set of modifiers to hold
        """
        if modifiers is None:
            modifiers = set()

        try:
            if self.backend == 'x11':
                await self._press_key_x11(key, modifiers)
            else:
                await self._press_key_wayland(key, modifiers)
        except Exception as e:
            self.logger.error(f"Error pressing key {key}: {e}")

    async def _press_key_x11(self, key: str, modifiers: Set[KeyModifier]):
        """Press key using xdotool (X11)"""
        # Build xdotool command
        mod_args = []
        for mod in modifiers:
            if mod == KeyModifier.CTRL:
                mod_args.append("ctrl")
            elif mod == KeyModifier.ALT:
                mod_args.append("alt")
            elif mod == KeyModifier.SHIFT:
                mod_args.append("shift")
            elif mod == KeyModifier.SUPER:
                mod_args.append("super")

        if mod_args:
            cmd = ["xdotool", "key", "+".join(mod_args + [key])]
        else:
            cmd = ["xdotool", "key", key]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()

    async def _press_key_wayland(self, key: str, modifiers: Set[KeyModifier]):
        """
        Press key under Wayland using ydotool

        Note: Requires ydotool to be installed and running
        """
        # Build ydotool command
        mod_args = []
        for mod in modifiers:
            if mod == KeyModifier.CTRL:
                mod_args.append("29")  # Left Ctrl keycode
            elif mod == KeyModifier.ALT:
                mod_args.append("56")  # Left Alt keycode
            elif mod == KeyModifier.SHIFT:
                mod_args.append("42")  # Left Shift keycode
            elif mod == KeyModifier.SUPER:
                mod_args.append("125")  # Left Super keycode

        # This is a simplified implementation
        # In production, you'd need proper keycode mapping
        cmd = ["ydotool", "key"]
        if mod_args:
            for mod in mod_args:
                cmd.extend([f"{mod}:1"])
        cmd.append(f"{key}:1")
        cmd.append(f"{key}:0")
        if mod_args:
            for mod in mod_args:
                cmd.extend([f"{mod}:0"])

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()

    async def type_text(self, text: str, delay: float = 0.05):
        """
        Type text with optional delay between characters

        Args:
            text: Text to type
            delay: Delay between characters in seconds
        """
        try:
            if self.backend == 'x11':
                # Use xdotool type command
                cmd = ["xdotool", "type", "--delay", str(int(delay * 1000)), text]
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()
            else:
                # Wayland: type character by character
                for char in text:
                    await self._press_key_wayland(char, set())
                    await asyncio.sleep(delay)

            self.logger.debug(f"Typed text: {text[:50]}...")

        except Exception as e:
            self.logger.error(f"Error typing text: {e}")

    async def send_combination(self, keys: List[str]):
        """
        Send a key combination

        Args:
            keys: List of keys to press simultaneously (e.g., ['ctrl', 'c'])
        """
        if self.backend == 'x11':
            cmd = ["xdotool", "key", "+".join(keys)]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.wait()
        else:
            # Simplified Wayland implementation
            self.logger.warning("Key combinations on Wayland require manual implementation")


class HotkeyManager:
    """
    Hotkey Manager - Register and handle global hotkeys

    Note: Global hotkey monitoring requires additional permissions
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._hotkeys: Dict[str, Callable] = {}
        self._running = False

    def register(self, hotkey: str, callback: Callable):
        """
        Register a hotkey

        Args:
            hotkey: Hotkey string (e.g., 'ctrl+shift+a')
            callback: Callback function to call when hotkey is pressed
        """
        self._hotkeys[hotkey.lower()] = callback
        self.logger.info(f"Registered hotkey: {hotkey}")

    def unregister(self, hotkey: str):
        """Unregister a hotkey"""
        if hotkey.lower() in self._hotkeys:
            del self._hotkeys[hotkey.lower()]
            self.logger.info(f"Unregistered hotkey: {hotkey}")

    async def start_monitoring(self):
        """
        Start monitoring for hotkeys

        Note: This is a simplified implementation.
        In production, you'd use xinput or evdev for monitoring.
        """
        self._running = True
        self.logger.info("Hotkey monitoring started (stub implementation)")

        # Stub implementation - in production would monitor actual key events
        while self._running:
            await asyncio.sleep(1)

    def stop_monitoring(self):
        """Stop monitoring for hotkeys"""
        self._running = False
        self.logger.info("Hotkey monitoring stopped")
