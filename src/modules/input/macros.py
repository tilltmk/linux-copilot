"""
Macro Engine - Record and replay input sequences
Supports keyboard and mouse macros with timing
"""

import logging
import asyncio
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import time


class MacroActionType(Enum):
    """Types of macro actions"""
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    MOUSE_SCROLL = "mouse_scroll"
    DELAY = "delay"
    TEXT_TYPE = "text_type"


@dataclass
class MacroAction:
    """Single action in a macro"""
    action_type: MacroActionType
    params: Dict[str, Any]
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "action_type": self.action_type.value,
            "params": self.params,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MacroAction':
        """Create from dictionary"""
        return cls(
            action_type=MacroActionType(data["action_type"]),
            params=data["params"],
            timestamp=data.get("timestamp", 0.0)
        )


@dataclass
class Macro:
    """Recorded macro sequence"""
    name: str
    actions: List[MacroAction]
    description: str = ""
    repeat_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "description": self.description,
            "repeat_count": self.repeat_count,
            "actions": [action.to_dict() for action in self.actions]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Macro':
        """Create from dictionary"""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            repeat_count=data.get("repeat_count", 1),
            actions=[MacroAction.from_dict(a) for a in data["actions"]]
        )


class MacroEngine:
    """
    Macro Engine - Record and replay input macros

    Features:
    - Record keyboard and mouse actions
    - Replay with accurate timing
    - Save/load macros to/from files
    - Macro editing and composition
    """

    def __init__(self, keyboard_controller, mouse_controller):
        self.logger = logging.getLogger(__name__)
        self.keyboard = keyboard_controller
        self.mouse = mouse_controller

        self._recording = False
        self._current_macro: Optional[List[MacroAction]] = None
        self._start_time: float = 0.0

        self._macros: Dict[str, Macro] = {}

    def start_recording(self):
        """Start recording a new macro"""
        if self._recording:
            self.logger.warning("Already recording a macro")
            return

        self._recording = True
        self._current_macro = []
        self._start_time = time.time()
        self.logger.info("Started macro recording")

    def stop_recording(self, name: str, description: str = "") -> Macro:
        """
        Stop recording and save macro

        Args:
            name: Name for the macro
            description: Optional description

        Returns:
            The recorded macro
        """
        if not self._recording:
            self.logger.warning("Not currently recording")
            return None

        self._recording = False

        macro = Macro(
            name=name,
            description=description,
            actions=self._current_macro
        )

        self._macros[name] = macro
        self.logger.info(f"Stopped recording macro '{name}' with {len(macro.actions)} actions")

        return macro

    def add_action(
        self,
        action_type: MacroActionType,
        params: Dict[str, Any]
    ):
        """
        Add an action to the current recording

        Args:
            action_type: Type of action
            params: Action parameters
        """
        if not self._recording:
            return

        timestamp = time.time() - self._start_time
        action = MacroAction(
            action_type=action_type,
            params=params,
            timestamp=timestamp
        )

        self._current_macro.append(action)

    async def replay_macro(
        self,
        macro_name: str,
        speed: float = 1.0,
        repeat: Optional[int] = None
    ):
        """
        Replay a recorded macro

        Args:
            macro_name: Name of macro to replay
            speed: Playback speed multiplier (1.0 = normal, 2.0 = double speed)
            repeat: Number of times to repeat (None = use macro's repeat_count)
        """
        if macro_name not in self._macros:
            self.logger.error(f"Macro '{macro_name}' not found")
            return

        macro = self._macros[macro_name]
        repeat_count = repeat if repeat is not None else macro.repeat_count

        self.logger.info(
            f"Replaying macro '{macro_name}' "
            f"{repeat_count} time(s) at {speed}x speed"
        )

        for i in range(repeat_count):
            last_timestamp = 0.0

            for action in macro.actions:
                # Calculate delay
                delay = (action.timestamp - last_timestamp) / speed
                if delay > 0:
                    await asyncio.sleep(delay)

                # Execute action
                await self._execute_action(action)

                last_timestamp = action.timestamp

            self.logger.debug(f"Completed replay iteration {i + 1}/{repeat_count}")

    async def _execute_action(self, action: MacroAction):
        """Execute a single macro action"""
        try:
            if action.action_type == MacroActionType.KEY_PRESS:
                await self.keyboard.press_key(
                    action.params["key"],
                    action.params.get("modifiers")
                )

            elif action.action_type == MacroActionType.TEXT_TYPE:
                await self.keyboard.type_text(action.params["text"])

            elif action.action_type == MacroActionType.MOUSE_MOVE:
                await self.mouse.move(
                    action.params["x"],
                    action.params["y"]
                )

            elif action.action_type == MacroActionType.MOUSE_CLICK:
                from .mouse import MouseButton
                button = MouseButton(action.params["button"])
                await self.mouse.click(button, action.params.get("clicks", 1))

            elif action.action_type == MacroActionType.MOUSE_SCROLL:
                await self.mouse.scroll(action.params["amount"])

            elif action.action_type == MacroActionType.DELAY:
                await asyncio.sleep(action.params["duration"])

        except Exception as e:
            self.logger.error(f"Error executing macro action: {e}")

    def save_macro(self, macro_name: str, file_path: Path):
        """
        Save a macro to a file

        Args:
            macro_name: Name of macro to save
            file_path: Path to save to
        """
        if macro_name not in self._macros:
            self.logger.error(f"Macro '{macro_name}' not found")
            return

        macro = self._macros[macro_name]

        try:
            with open(file_path, 'w') as f:
                json.dump(macro.to_dict(), f, indent=2)

            self.logger.info(f"Saved macro '{macro_name}' to {file_path}")

        except Exception as e:
            self.logger.error(f"Error saving macro: {e}")

    def load_macro(self, file_path: Path) -> Optional[Macro]:
        """
        Load a macro from a file

        Args:
            file_path: Path to load from

        Returns:
            Loaded macro or None if error
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            macro = Macro.from_dict(data)
            self._macros[macro.name] = macro

            self.logger.info(
                f"Loaded macro '{macro.name}' with {len(macro.actions)} actions"
            )

            return macro

        except Exception as e:
            self.logger.error(f"Error loading macro: {e}")
            return None

    def list_macros(self) -> List[str]:
        """Get list of available macro names"""
        return list(self._macros.keys())

    def get_macro(self, name: str) -> Optional[Macro]:
        """Get a macro by name"""
        return self._macros.get(name)

    def delete_macro(self, name: str):
        """Delete a macro"""
        if name in self._macros:
            del self._macros[name]
            self.logger.info(f"Deleted macro '{name}'")
