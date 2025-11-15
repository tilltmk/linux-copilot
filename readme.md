# Linux Agentic Copilot

> A highly integrated, modular system-level automation framework for Linux with Wayland and X11 support

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux-lightgrey.svg)](https://www.linux.org/)

Linux Agentic Copilot is a powerful, modular automation framework that operates at the system level, providing comprehensive control over window management, input devices, screen capture, and extensible automation through a plugin system.

## Features

### Core Capabilities

- **Event-Driven Architecture** - Reactive system monitoring and event handling
- **Modular Design** - Clean separation of concerns with pluggable modules
- **Cross-Platform Display Support** - Works with both X11 and Wayland
- **Security-First** - Permission management, sandboxing, and audit logging
- **Extensible Plugin System** - Dynamic loading/unloading of custom plugins

### Functional Modules

#### Window & Desktop Management
- List, activate, and manipulate windows
- Move, resize, maximize, minimize windows
- Virtual desktop management
- Window event monitoring
- Find windows by title or class

#### Input Control
- **Keyboard**: Key press simulation, text typing, key combinations, hotkeys
- **Mouse**: Movement, clicking, scrolling, dragging
- **Macros**: Record and replay input sequences with accurate timing
- **Hotkeys**: Global hotkey registration and monitoring

#### Screen Capture
- **Screenshots**: Fullscreen, window, region, interactive selection
- **Recording**: Screen recording with audio support
- Multiple format support (PNG, JPG, MP4)
- Wayland and X11 compatible

#### Logging & Security
- Multi-target logging (console, file, syslog)
- Log rotation and structured logging
- Audit logging for security events
- Permission management and sandboxing
- Input sanitization and validation

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/linux-copilot.git
cd linux-copilot

# Run the automatic installer
./install.sh
```

### Basic Usage

```python
import asyncio
from src.copilot import LinuxCopilot

async def main():
    # Initialize copilot
    copilot = LinuxCopilot()
    await copilot.initialize()

    # Use keyboard module
    keyboard = copilot.get_module('keyboard')
    await keyboard.type_text("Hello, World!")

    # Use window manager
    wm = copilot.get_module('windows')
    windows = await wm.get_all_windows()
    for window in windows:
        print(f"{window.title} - {window.wm_class}")

    # Take a screenshot
    screenshot = copilot.get_module('screenshot')
    path = await screenshot.capture_fullscreen()
    print(f"Screenshot saved to {path}")

    # Cleanup
    await copilot.stop()

asyncio.run(main())
```

## Architecture

```
linux-copilot/
├── src/
│   ├── core/                    # Core framework
│   │   ├── event_loop.py        # Event-driven processing
│   │   ├── security.py          # Security & permissions
│   │   └── plugin_api.py        # Plugin system
│   ├── modules/                 # Feature modules
│   │   ├── input/               # Keyboard, mouse, macros
│   │   ├── window/              # Window management
│   │   ├── screenshot/          # Screen capture & recording
│   │   └── logging/             # Logging system
│   ├── plugins/                 # Plugin directory
│   │   └── examples/            # Example plugins
│   └── copilot.py              # Main application
├── tests/                       # Test suite
├── docs/                        # Documentation
├── config/                      # Configuration files
└── install.sh                   # Installation script
```

## Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Complete installation instructions
- **[User Guide](docs/USER_GUIDE.md)** - How to use the copilot
- **[API Documentation](docs/API.md)** - Complete API reference
- **[Plugin Development](docs/API.md#plugin-api)** - Create your own plugins

## Example Use Cases

### Window Automation

```python
# Arrange windows in a grid layout
wm = copilot.get_module('windows')
windows = await wm.get_all_windows()

positions = [(0, 0), (960, 0), (0, 540), (960, 540)]
for i, window in enumerate(windows[:4]):
    x, y = positions[i]
    await wm.move_window(window.window_id, x, y)
    await wm.resize_window(window.window_id, 960, 540)
```

### Macro Recording & Playback

```python
# Record a macro
macros = copilot.get_module('macros')
macros.start_recording()

# Perform actions...
await keyboard.type_text("import asyncio")
await keyboard.press_key("Return", set())

# Save and replay
macro = macros.stop_recording("python_import")
await macros.replay_macro("python_import", speed=2.0)
```

### Automated Screenshots

```python
# Take a screenshot of a specific application
window = await wm.get_window_by_class("firefox")
if window:
    await wm.activate_window(window.window_id)
    await asyncio.sleep(0.5)
    path = await screenshot.capture_window(window.window_id)
```

## Plugin Examples

### Window Automation Plugin

```python
class WindowAutomationPlugin(PluginBase):
    async def initialize(self, core_api):
        self.wm = core_api.get_module('windows')
        core_api.subscribe_event("arrange_windows", self._arrange)
        return True

    async def _arrange(self, event):
        windows = await self.wm.get_all_windows()
        # Arrange in grid...
```

See `src/plugins/examples/` for complete working examples.

## System Requirements

- **OS**: Linux with X11 or Wayland
- **Python**: 3.8 or higher
- **System Packages**: xdotool, wmctrl, scrot/maim (X11) or grim, slurp, ydotool (Wayland)

## Supported Distributions

- Ubuntu 20.04+
- Debian 11+
- Fedora 35+
- Arch Linux
- openSUSE
- Other systemd-based distributions

## Security

Linux Copilot implements multiple security layers:

- **Permission Management**: Operations are classified by risk level
- **Sandboxing**: Plugins run with limited permissions
- **Input Validation**: All inputs are sanitized
- **Audit Logging**: Security-relevant events are logged
- **Minimal Privileges**: Runs with minimal necessary permissions

## Testing

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
cd tests
./run_tests.sh

# Run specific test
pytest tests/test_core.py -v
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Roadmap

- [ ] Additional Wayland compositor support (Hyprland, KWin)
- [ ] GUI configuration tool
- [ ] Voice command integration
- [ ] AI-powered automation suggestions
- [ ] Cross-desktop protocol standardization
- [ ] Mobile app for remote control
- [ ] Community plugin repository

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Python's asyncio for high-performance event handling
- Uses xdotool, wmctrl for X11 support
- Uses grim, slurp, ydotool for Wayland support
- Inspired by automation tools like AutoHotkey and Hammerspoon

## Support

- **Documentation**: Check the `docs/` directory
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Join our discussion forum
- **Email**: support@linux-copilot.org

## Project Status

**Status**: Alpha - Active Development

This project is actively developed and tested on Ubuntu 22.04, Fedora 38, and Arch Linux. While functional, the API may change between releases.

---

**Made with ❤️ by the Linux Copilot Project**
