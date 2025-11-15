# API Documentation - Linux Agentic Copilot

Complete API reference for all modules and classes.

## Table of Contents

1. [Core API](#core-api)
2. [Input Modules](#input-modules)
3. [Window Module](#window-module)
4. [Screenshot Module](#screenshot-module)
5. [Plugin API](#plugin-api)

---

## Core API

### LinuxCopilot

Main application class.

#### Constructor

```python
LinuxCopilot(
    log_dir: Optional[Path] = None,
    plugin_dir: Optional[Path] = None,
    config_dir: Optional[Path] = None
)
```

#### Methods

```python
async def initialize() -> None
```
Initialize the copilot and all subsystems.

```python
async def start() -> None
```
Start the copilot.

```python
async def stop() -> None
```
Stop the copilot gracefully.

```python
async def run() -> None
```
Run the copilot until stopped (blocking).

```python
def get_module(module_name: str) -> Any
```
Get a module by name.

```python
def emit_event(
    event_type: str,
    data: dict,
    priority: EventPriority = EventPriority.NORMAL
) -> None
```
Emit a custom event.

---

### EventLoop

Event-driven processing system.

#### Methods

```python
async def start() -> None
```
Start the event loop.

```python
async def stop() -> None
```
Stop the event loop.

```python
def subscribe(event_type: str, callback: Callable) -> None
```
Subscribe to an event type.

```python
def unsubscribe(event_type: str, callback: Callable) -> None
```
Unsubscribe from an event type.

```python
def emit(event: Event) -> None
```
Emit an event (thread-safe).

---

### SecurityManager

Security and permission management.

#### Methods

```python
def check_permission(
    operation: str,
    required_level: PermissionLevel = PermissionLevel.USER
) -> bool
```
Check if an operation is permitted.

```python
def whitelist_operation(operation: str) -> None
```
Whitelist a specific operation.

```python
def blacklist_operation(operation: str) -> None
```
Blacklist a specific operation.

```python
def sanitize_input(input_str: str) -> str
```
Sanitize user input to prevent injection attacks.

```python
def validate_path(
    path: str,
    allow_absolute: bool = True
) -> bool
```
Validate a file path for security.

```python
def audit_log(
    operation: str,
    details: str,
    level: str = "INFO"
) -> None
```
Log security-relevant operations.

---

## Input Modules

### KeyboardController

Keyboard input control.

#### Methods

```python
async def press_key(
    key: str,
    modifiers: Optional[Set[KeyModifier]] = None
) -> None
```
Press a key with optional modifiers.

**Parameters**:
- `key`: Key to press (e.g., 'a', 'Return', 'Escape')
- `modifiers`: Set of KeyModifier (CTRL, ALT, SHIFT, SUPER)

**Example**:
```python
await keyboard.press_key('c', {KeyModifier.CTRL})
```

```python
async def type_text(text: str, delay: float = 0.05) -> None
```
Type text with optional delay between characters.

```python
async def send_combination(keys: List[str]) -> None
```
Send a key combination.

**Example**:
```python
await keyboard.send_combination(['ctrl', 'alt', 't'])
```

---

### MouseController

Mouse input control.

#### Methods

```python
async def get_position() -> Tuple[int, int]
```
Get current mouse position.

**Returns**: Tuple of (x, y) coordinates

```python
async def move(x: int, y: int, relative: bool = False) -> None
```
Move mouse to position.

**Parameters**:
- `x`: X coordinate
- `y`: Y coordinate
- `relative`: If True, move relative to current position

```python
async def click(
    button: MouseButton = MouseButton.LEFT,
    clicks: int = 1
) -> None
```
Simulate mouse click.

```python
async def scroll(amount: int) -> None
```
Simulate mouse scroll.

**Parameters**:
- `amount`: Scroll amount (positive for up, negative for down)

```python
async def drag(
    from_x: int, from_y: int,
    to_x: int, to_y: int
) -> None
```
Simulate mouse drag.

---

### MacroEngine

Macro recording and playback.

#### Methods

```python
def start_recording() -> None
```
Start recording a new macro.

```python
def stop_recording(
    name: str,
    description: str = ""
) -> Macro
```
Stop recording and save macro.

```python
def add_action(
    action_type: MacroActionType,
    params: Dict[str, Any]
) -> None
```
Add an action to the current recording.

```python
async def replay_macro(
    macro_name: str,
    speed: float = 1.0,
    repeat: Optional[int] = None
) -> None
```
Replay a recorded macro.

```python
def save_macro(macro_name: str, file_path: Path) -> None
```
Save a macro to a file.

```python
def load_macro(file_path: Path) -> Optional[Macro]
```
Load a macro from a file.

```python
def list_macros() -> List[str]
```
Get list of available macro names.

---

### HotkeyManager

Global hotkey management.

#### Methods

```python
def register(hotkey: str, callback: Callable) -> None
```
Register a hotkey.

**Parameters**:
- `hotkey`: Hotkey string (e.g., 'ctrl+shift+a')
- `callback`: Callback function to call when hotkey is pressed

```python
def unregister(hotkey: str) -> None
```
Unregister a hotkey.

```python
async def start_monitoring() -> None
```
Start monitoring for hotkeys.

```python
def stop_monitoring() -> None
```
Stop monitoring for hotkeys.

---

## Window Module

### WindowManager

Window management for X11 and Wayland.

#### Methods

```python
async def get_all_windows() -> List[WindowInfo]
```
Get information about all windows.

```python
async def get_active_window() -> Optional[WindowInfo]
```
Get the currently active window.

```python
async def activate_window(window_id: str) -> None
```
Activate (focus) a window.

```python
async def close_window(window_id: str) -> None
```
Close a window.

```python
async def move_window(window_id: str, x: int, y: int) -> None
```
Move a window to specific position.

```python
async def resize_window(
    window_id: str,
    width: int,
    height: int
) -> None
```
Resize a window.

```python
async def maximize_window(window_id: str) -> None
```
Maximize a window.

```python
async def minimize_window(window_id: str) -> None
```
Minimize a window.

```python
async def get_window_by_title(
    title_pattern: str
) -> Optional[WindowInfo]
```
Find a window by title pattern (regex).

```python
async def get_window_by_class(wm_class: str) -> Optional[WindowInfo]
```
Find a window by WM_CLASS.

---

### WindowInfo

Window information dataclass.

#### Attributes

- `window_id: str` - Window identifier
- `title: str` - Window title
- `wm_class: str` - Window class
- `pid: int` - Process ID
- `x: int` - X position
- `y: int` - Y position
- `width: int` - Width
- `height: int` - Height
- `desktop: int` - Virtual desktop number
- `state: WindowState` - Window state
- `is_active: bool` - Whether window is active

---

## Screenshot Module

### ScreenshotCapture

Screenshot capture.

#### Methods

```python
async def capture_fullscreen(
    output_path: Optional[Path] = None,
    format: str = "png"
) -> Path
```
Capture fullscreen screenshot.

```python
async def capture_window(
    window_id: Optional[str] = None,
    output_path: Optional[Path] = None,
    format: str = "png"
) -> Path
```
Capture screenshot of a specific window.

```python
async def capture_region(
    x: int, y: int,
    width: int, height: int,
    output_path: Optional[Path] = None,
    format: str = "png"
) -> Path
```
Capture screenshot of a specific region.

```python
async def capture_interactive(
    output_path: Optional[Path] = None,
    format: str = "png"
) -> Path
```
Interactive screenshot selection (user selects region).

---

### ScreenRecorder

Screen recording.

#### Methods

```python
async def start_recording(
    output_path: Optional[Path] = None,
    fps: int = 30,
    audio: bool = False
) -> Path
```
Start screen recording.

```python
async def stop_recording() -> Optional[Path]
```
Stop screen recording.

```python
def is_recording() -> bool
```
Check if currently recording.

---

## Plugin API

### PluginBase

Base class for all plugins.

#### Methods to Implement

```python
def get_metadata(self) -> PluginMetadata
```
Return plugin metadata.

```python
async def initialize(self, core_api: CoreAPI) -> bool
```
Initialize the plugin.

```python
async def shutdown(self) -> None
```
Shutdown the plugin and cleanup resources.

#### Helper Methods

```python
def is_initialized() -> bool
```
Check if plugin is initialized.

```python
def is_enabled() -> bool
```
Check if plugin is enabled.

```python
def enable() -> None
```
Enable the plugin.

```python
def disable() -> None
```
Disable the plugin.

---

### PluginManager

Plugin management.

#### Methods

```python
def load_plugin(plugin_path: Path) -> bool
```
Load a plugin from a file path.

```python
async def initialize_plugin(plugin_name: str) -> bool
```
Initialize a loaded plugin.

```python
async def unload_plugin(plugin_name: str) -> bool
```
Unload a plugin.

```python
def load_plugins_from_directory(directory: Path) -> int
```
Load all plugins from a directory.

```python
def get_plugin(plugin_name: str) -> Optional[PluginBase]
```
Get a loaded plugin by name.

```python
def list_plugins() -> List[str]
```
List all loaded plugin names.

```python
def get_plugin_info(plugin_name: str) -> Optional[Dict[str, Any]]
```
Get information about a plugin.

---

### CoreAPI

API interface provided to plugins.

#### Attributes

- `event_loop: EventLoop` - Event loop instance
- `security: SecurityManager` - Security manager instance
- `modules: Dict` - Module registry

#### Methods

```python
def subscribe_event(event_type: str, callback: Callable) -> None
```
Subscribe to an event.

```python
def emit_event(event: Event) -> None
```
Emit an event.

```python
def get_module(module_name: str) -> Optional[Any]
```
Get a registered module.

```python
def check_permission(operation: str, level: PermissionLevel) -> bool
```
Check if an operation is permitted.

---

## Enumerations

### EventPriority

```python
class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3
```

### PermissionLevel

```python
class PermissionLevel(Enum):
    USER = 0          # Normal user operations
    ELEVATED = 1      # Requires user confirmation
    DANGEROUS = 2     # Requires explicit authorization
    ROOT = 3          # Requires root privileges
```

### KeyModifier

```python
class KeyModifier(Enum):
    CTRL = "ctrl"
    ALT = "alt"
    SHIFT = "shift"
    SUPER = "super"
```

### MouseButton

```python
class MouseButton(Enum):
    LEFT = 1
    MIDDLE = 2
    RIGHT = 3
    SCROLL_UP = 4
    SCROLL_DOWN = 5
```

### MacroActionType

```python
class MacroActionType(Enum):
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    MOUSE_SCROLL = "mouse_scroll"
    DELAY = "delay"
    TEXT_TYPE = "text_type"
```

---

## Data Classes

### Event

```python
@dataclass
class Event:
    event_type: str
    data: Dict[str, Any]
    priority: EventPriority = EventPriority.NORMAL
    timestamp: float = 0.0
    source: Optional[str] = None
```

### PluginMetadata

```python
@dataclass
class PluginMetadata:
    name: str
    version: str
    author: str
    description: str
    dependencies: List[str] = []
```
