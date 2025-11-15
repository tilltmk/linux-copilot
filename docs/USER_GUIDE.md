# User Guide - Linux Agentic Copilot

Complete guide for using Linux Agentic Copilot.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Core Concepts](#core-concepts)
3. [Module Usage](#module-usage)
4. [Plugin Development](#plugin-development)
5. [Configuration](#configuration)
6. [Advanced Usage](#advanced-usage)

---

## Getting Started

### Starting the Copilot

```bash
# Activate virtual environment
source venv/bin/activate

# Start the copilot
python -m src.copilot
```

### Basic Usage Example

```python
import asyncio
from src.copilot import LinuxCopilot

async def main():
    # Create copilot instance
    copilot = LinuxCopilot()

    # Initialize
    await copilot.initialize()

    # Get a module
    keyboard = copilot.get_module('keyboard')

    # Use the keyboard
    await keyboard.type_text("Hello, World!")

    # Cleanup
    await copilot.stop()

asyncio.run(main())
```

---

## Core Concepts

### Event-Driven Architecture

Linux Copilot uses an event-driven architecture:

```python
from src.core.event_loop import Event, EventPriority

# Subscribe to events
copilot.event_loop.subscribe("window_changed", my_handler)

# Emit events
copilot.emit_event(
    "custom_event",
    {"data": "value"},
    priority=EventPriority.HIGH
)
```

### Security Model

All operations are subject to security checks:

```python
from src.core.security import PermissionLevel

# Check permissions
if copilot.security.check_permission("dangerous_op", PermissionLevel.DANGEROUS):
    # Perform operation
    pass
```

### Modular Architecture

Components are organized into modules:

- **Core**: Event loop, security, plugin API
- **Input**: Keyboard, mouse, macros, hotkeys
- **Window**: Window management (X11/Wayland)
- **Screenshot**: Screen capture and recording
- **Logging**: Multi-target logging system

---

## Module Usage

### Keyboard Module

```python
from src.modules.input.keyboard import KeyModifier

# Get keyboard controller
keyboard = copilot.get_module('keyboard')

# Type text
await keyboard.type_text("Hello!", delay=0.05)

# Press keys with modifiers
await keyboard.press_key('c', {KeyModifier.CTRL})

# Send key combination
await keyboard.send_combination(['ctrl', 'alt', 't'])
```

### Mouse Module

```python
from src.modules.input.mouse import MouseButton

# Get mouse controller
mouse = copilot.get_module('mouse')

# Get current position
x, y = await mouse.get_position()

# Move mouse
await mouse.move(100, 200)

# Click
await mouse.click(MouseButton.LEFT, clicks=2)

# Scroll
await mouse.scroll(5)  # Scroll up

# Drag
await mouse.drag(100, 100, 500, 500)
```

### Macro Module

```python
from src.modules.input.macros import MacroActionType

# Get macro engine
macros = copilot.get_module('macros')

# Record a macro
macros.start_recording()

# Perform actions...
macros.add_action(MacroActionType.TEXT_TYPE, {"text": "test"})
macros.add_action(MacroActionType.MOUSE_CLICK, {"button": 1, "clicks": 1})

# Stop and save
macro = macros.stop_recording("my_macro", "My first macro")

# Replay macro
await macros.replay_macro("my_macro", speed=1.0)

# Save to file
from pathlib import Path
macros.save_macro("my_macro", Path("my_macro.json"))

# Load from file
macros.load_macro(Path("my_macro.json"))
```

### Window Module

```python
# Get window manager
wm = copilot.get_module('windows')

# Get all windows
windows = await wm.get_all_windows()
for window in windows:
    print(f"{window.title} - {window.wm_class}")

# Get active window
active = await wm.get_active_window()
print(f"Active: {active.title}")

# Find window by title
window = await wm.get_window_by_title("Firefox")

# Manipulate window
if window:
    await wm.activate_window(window.window_id)
    await wm.move_window(window.window_id, 100, 100)
    await wm.resize_window(window.window_id, 800, 600)
    await wm.maximize_window(window.window_id)
```

### Screenshot Module

```python
from pathlib import Path

# Get screenshot module
screenshot = copilot.get_module('screenshot')

# Fullscreen capture
path = await screenshot.capture_fullscreen(
    output_path=Path("~/screenshot.png"),
    format="png"
)

# Window capture
path = await screenshot.capture_window(
    window_id=window.window_id,
    format="png"
)

# Region capture
path = await screenshot.capture_region(
    x=100, y=100,
    width=400, height=300
)

# Interactive selection
path = await screenshot.capture_interactive()
```

### Recording Module

```python
# Get recorder
recorder = copilot.get_module('recorder')

# Start recording
path = await recorder.start_recording(
    fps=30,
    audio=False
)

# ... do stuff ...

# Stop recording
saved_path = await recorder.stop_recording()
print(f"Recording saved to {saved_path}")
```

---

## Plugin Development

### Creating a Plugin

```python
from src.core.plugin_api import PluginBase, PluginMetadata

class MyPlugin(PluginBase):
    """My custom plugin"""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            author="Your Name",
            description="My awesome plugin",
            dependencies=[]
        )

    async def initialize(self, core_api) -> bool:
        """Initialize plugin"""
        self.core_api = core_api

        # Get modules
        self.keyboard = core_api.get_module('keyboard')

        # Subscribe to events
        core_api.subscribe_event("my_event", self._handle_event)

        self.logger.info("Plugin initialized")
        return True

    async def shutdown(self):
        """Cleanup"""
        self.logger.info("Plugin shutting down")

    async def _handle_event(self, event):
        """Handle custom event"""
        await self.keyboard.type_text("Event received!")
```

### Loading Plugins

```python
# Load plugin from file
from pathlib import Path

plugin_path = Path("~/.config/linux-copilot/plugins/my_plugin.py")
copilot.plugin_manager.load_plugin(plugin_path)

# Initialize plugin
await copilot.plugin_manager.initialize_plugin("my_plugin")

# List plugins
plugins = copilot.plugin_manager.list_plugins()

# Get plugin info
info = copilot.plugin_manager.get_plugin_info("my_plugin")

# Unload plugin
await copilot.plugin_manager.unload_plugin("my_plugin")
```

---

## Configuration

### Configuration File

Location: `~/.config/linux-copilot/config.json`

```json
{
  "logging": {
    "console_level": "INFO",
    "file_level": "DEBUG",
    "enable_syslog": false
  },
  "security": {
    "enable_sandboxing": true,
    "whitelist_operations": ["safe_op1", "safe_op2"],
    "blacklist_operations": ["dangerous_op"]
  },
  "plugins": {
    "auto_load": true,
    "enabled_plugins": [
      "window_automation",
      "screenshot_tool"
    ]
  },
  "input": {
    "keyboard": {
      "type_delay": 0.05
    }
  }
}
```

---

## Advanced Usage

### Event Monitoring

```python
# Monitor window changes
async def on_window_change(event):
    window = event.data.get('window')
    print(f"Window changed to: {window.title}")

copilot.event_loop.subscribe("window_changed", on_window_change)
```

### Hotkey Registration

```python
# Get hotkey manager
hotkeys = copilot.get_module('hotkeys')

# Register hotkey
def my_hotkey_handler():
    print("Hotkey pressed!")

hotkeys.register("ctrl+shift+a", my_hotkey_handler)

# Start monitoring
await hotkeys.start_monitoring()
```

### Automation Workflows

```python
async def automation_workflow():
    """Example automation workflow"""

    # 1. Find application window
    window = await wm.get_window_by_class("firefox")

    # 2. Activate it
    if window:
        await wm.activate_window(window.window_id)

    # 3. Wait a bit
    await asyncio.sleep(0.5)

    # 4. Type text
    await keyboard.type_text("https://example.com")

    # 5. Press Enter
    await keyboard.press_key("Return", set())

    # 6. Take screenshot
    await asyncio.sleep(2)
    await screenshot.capture_fullscreen()
```

---

## Best Practices

1. **Always use async/await**: All copilot operations are asynchronous
2. **Handle errors**: Wrap operations in try/except blocks
3. **Check permissions**: Use security manager for dangerous operations
4. **Clean up resources**: Always call `stop()` when done
5. **Use logging**: Log important operations for debugging
6. **Test plugins**: Test plugins in isolation before deployment

---

## Examples

See the `src/plugins/examples/` directory for complete working examples:

- `window_automation.py` - Window management automation
- `screenshot_tool.py` - Screenshot and recording automation
- `productivity_macros.py` - Text expansion and workflows

---

## Next Steps

- Read the [API Documentation](API.md)
- Check out [Plugin Development Guide](PLUGINS.md)
- Join the community and share your plugins!
