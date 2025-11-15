"""
Integration tests for Linux Agentic Copilot
Tests complete workflows and module interactions
"""

import pytest
import asyncio
from pathlib import Path
import tempfile

from src.copilot import LinuxCopilot
from src.core.event_loop import Event, EventPriority


class TestLinuxCopilotIntegration:
    """Integration tests for the main copilot"""

    @pytest.mark.asyncio
    async def test_copilot_initialization(self):
        """Test copilot initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            copilot = LinuxCopilot(
                log_dir=Path(tmpdir) / "logs",
                plugin_dir=Path(tmpdir) / "plugins",
                config_dir=Path(tmpdir) / "config"
            )

            await copilot.initialize()
            assert copilot._initialized is True

            await copilot.stop()

    @pytest.mark.asyncio
    async def test_copilot_modules(self):
        """Test accessing copilot modules"""
        with tempfile.TemporaryDirectory() as tmpdir:
            copilot = LinuxCopilot(
                log_dir=Path(tmpdir) / "logs",
                plugin_dir=Path(tmpdir) / "plugins",
                config_dir=Path(tmpdir) / "config"
            )

            await copilot.initialize()

            # Check that all modules are available
            assert copilot.get_module('keyboard') is not None
            assert copilot.get_module('mouse') is not None
            assert copilot.get_module('windows') is not None
            assert copilot.get_module('screenshot') is not None
            assert copilot.get_module('recorder') is not None
            assert copilot.get_module('macros') is not None

            await copilot.stop()

    @pytest.mark.asyncio
    async def test_event_emission(self):
        """Test event emission through copilot"""
        with tempfile.TemporaryDirectory() as tmpdir:
            copilot = LinuxCopilot(
                log_dir=Path(tmpdir) / "logs",
                plugin_dir=Path(tmpdir) / "plugins",
                config_dir=Path(tmpdir) / "config"
            )

            await copilot.initialize()

            received_events = []

            async def handler(event):
                received_events.append(event)

            copilot.event_loop.subscribe("test_event", handler)

            # Emit event
            copilot.emit_event("test_event", {"data": "test"})

            # Wait for processing
            await asyncio.sleep(0.5)

            assert len(received_events) == 1
            assert received_events[0].data["data"] == "test"

            await copilot.stop()


class TestEndToEndWorkflows:
    """End-to-end workflow tests"""

    @pytest.mark.asyncio
    async def test_macro_workflow(self):
        """Test complete macro creation and replay workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            copilot = LinuxCopilot(
                log_dir=Path(tmpdir) / "logs",
                plugin_dir=Path(tmpdir) / "plugins",
                config_dir=Path(tmpdir) / "config"
            )

            await copilot.initialize()

            macro_engine = copilot.get_module('macros')

            # Create a simple macro
            macro_engine.start_recording()
            from src.modules.input.macros import MacroActionType
            macro_engine.add_action(MacroActionType.TEXT_TYPE, {"text": "hello"})
            macro = macro_engine.stop_recording("test_macro", "Test workflow")

            assert macro is not None
            assert len(macro.actions) == 1

            # Save macro
            macro_file = Path(tmpdir) / "test_macro.json"
            macro_engine.save_macro("test_macro", macro_file)
            assert macro_file.exists()

            # Load macro
            loaded_macro = macro_engine.load_macro(macro_file)
            assert loaded_macro is not None
            assert loaded_macro.name == "test_macro"

            await copilot.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
