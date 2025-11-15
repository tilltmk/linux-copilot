"""
Tests for modules (Input, Window, Screenshot)
"""

import pytest
import asyncio

from src.modules.input.keyboard import KeyboardController, KeyModifier
from src.modules.input.mouse import MouseController, MouseButton
from src.modules.input.macros import MacroEngine, Macro, MacroAction, MacroActionType
from src.modules.window.manager import WindowManager


class TestKeyboardController:
    """Test KeyboardController functionality"""

    def test_keyboard_creation(self):
        """Test keyboard controller creation"""
        keyboard = KeyboardController()
        assert keyboard is not None
        assert keyboard.backend in ['x11', 'wayland']


class TestMouseController:
    """Test MouseController functionality"""

    def test_mouse_creation(self):
        """Test mouse controller creation"""
        mouse = MouseController()
        assert mouse is not None
        assert mouse.backend in ['x11', 'wayland']


class TestMacroEngine:
    """Test MacroEngine functionality"""

    def test_macro_engine_creation(self):
        """Test macro engine creation"""
        keyboard = KeyboardController()
        mouse = MouseController()
        macro_engine = MacroEngine(keyboard, mouse)

        assert macro_engine is not None
        assert len(macro_engine.list_macros()) == 0

    def test_macro_recording(self):
        """Test macro recording"""
        keyboard = KeyboardController()
        mouse = MouseController()
        macro_engine = MacroEngine(keyboard, mouse)

        # Start recording
        macro_engine.start_recording()
        assert macro_engine._recording is True

        # Add some actions
        macro_engine.add_action(
            MacroActionType.TEXT_TYPE,
            {"text": "test"}
        )

        # Stop recording
        macro = macro_engine.stop_recording("test_macro", "Test macro")
        assert macro is not None
        assert macro.name == "test_macro"
        assert len(macro.actions) == 1
        assert macro_engine._recording is False

    def test_macro_serialization(self):
        """Test macro serialization"""
        action = MacroAction(
            action_type=MacroActionType.TEXT_TYPE,
            params={"text": "test"},
            timestamp=1.0
        )

        # Serialize
        action_dict = action.to_dict()
        assert action_dict["action_type"] == "text_type"
        assert action_dict["params"]["text"] == "test"

        # Deserialize
        action2 = MacroAction.from_dict(action_dict)
        assert action2.action_type == MacroActionType.TEXT_TYPE
        assert action2.params["text"] == "test"

    def test_macro_list(self):
        """Test listing macros"""
        keyboard = KeyboardController()
        mouse = MouseController()
        macro_engine = MacroEngine(keyboard, mouse)

        # Create a macro
        macro_engine.start_recording()
        macro_engine.add_action(MacroActionType.TEXT_TYPE, {"text": "test"})
        macro_engine.stop_recording("test1")

        # List macros
        macros = macro_engine.list_macros()
        assert len(macros) == 1
        assert "test1" in macros


class TestWindowManager:
    """Test WindowManager functionality"""

    def test_window_manager_creation(self):
        """Test window manager creation"""
        wm = WindowManager()
        assert wm is not None
        assert wm.backend in ['x11', 'wayland']

    @pytest.mark.asyncio
    async def test_get_all_windows(self):
        """Test getting all windows"""
        wm = WindowManager()
        windows = await wm.get_all_windows()

        # Should return a list (might be empty in test environment)
        assert isinstance(windows, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
