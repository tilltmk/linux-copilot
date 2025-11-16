# Linux Copilot - Quick Start Guide

## Installation

### Automatic Installation (Recommended)

The easiest way to install Linux Copilot is using the automatic installation script:

```bash
git clone https://github.com/yourusername/linux-copilot.git
cd linux-copilot
chmod +x install_advanced.sh
sudo ./install_advanced.sh
```

This script will:
- Auto-detect your Linux distribution
- Install all required dependencies
- Build the C++ core with optimizations
- Build the Qt6 UI
- Run tests
- Install to system or user directories
- Configure the environment

Supported distributions:
- **Fedora** 35+
- **openSUSE** Leap 15.4+, Tumbleweed
- **Debian** 11+
- **Ubuntu** 20.04+
- **Arch Linux** / Manjaro

### Manual Installation

If you prefer manual installation:

#### 1. Install Dependencies

**Fedora:**
```bash
sudo dnf install gcc-c++ cmake ninja-build \
    qt6-qtbase-devel python3-devel \
    libX11-devel libXi-devel libXtst-devel libXrandr-devel \
    xdotool wmctrl scrot
```

**Ubuntu/Debian:**
```bash
sudo apt install build-essential cmake ninja-build \
    qt6-base-dev python3-dev \
    libx11-dev libxi-dev libxtst-dev libxrandr-dev \
    xdotool wmctrl scrot maim
```

**Arch Linux:**
```bash
sudo pacman -S base-devel cmake ninja \
    qt6-base python \
    libx11 libxi libxtst libxrandr \
    xdotool wmctrl scrot
```

#### 2. Install Python Dependencies

```bash
pip3 install --user pybind11 asyncio-mqtt pydantic python-xlib pytest
```

#### 3. Build

```bash
mkdir build && cd build
cmake .. -G Ninja -DCMAKE_BUILD_TYPE=Release
ninja -j$(nproc)
```

#### 4. Install

```bash
sudo ninja install
# Or for user installation:
DESTDIR=$HOME/.local ninja install
```

## First Launch

### GUI Mode

Launch the graphical user interface:

```bash
copilot-ui
```

The main window will appear with the dashboard showing:
- Loaded plugins
- System status
- AI model selection
- Quick actions
- Event log

The application will also appear in your system tray for quick access.

### CLI Mode

For command-line usage:

```bash
copilot-cli --help
```

### Daemon Mode

Run as a background service:

```bash
copilot --daemon
```

Enable auto-start on login:

```bash
systemctl --user enable copilot.service
systemctl --user start copilot.service
```

## Basic Usage

### Window Management

#### List All Windows

```python
import asyncio
from src.copilot import LinuxCopilot

async def main():
    copilot = LinuxCopilot()
    await copilot.initialize()

    wm = copilot.get_module('windows')
    windows = await wm.get_all_windows()

    for window in windows:
        print(f"{window.title} - {window.wm_class}")

    await copilot.stop()

asyncio.run(main())
```

#### Arrange Windows in Grid

```python
# Arrange all windows in 2x2 grid
wm = copilot.get_module('windows')
windows = await wm.get_all_windows()

positions = [
    (0, 0, 960, 540),      # Top-left
    (960, 0, 960, 540),    # Top-right
    (0, 540, 960, 540),    # Bottom-left
    (960, 540, 960, 540)   # Bottom-right
]

for i, window in enumerate(windows[:4]):
    x, y, w, h = positions[i]
    await wm.set_window_geometry(window.window_id, x, y, w, h)
```

### Input Automation

#### Type Text

```python
keyboard = copilot.get_module('keyboard')
await keyboard.type_text("Hello, World!")
```

#### Press Key Combination

```python
await keyboard.press_key("c", {"ctrl"})  # Ctrl+C
```

#### Move Mouse

```python
mouse = copilot.get_module('mouse')
await mouse.move_to(500, 300)
await mouse.click()
```

### Screenshot

#### Capture Fullscreen

```python
screenshot = copilot.get_module('screenshot')
path = await screenshot.capture_fullscreen()
print(f"Screenshot saved to: {path}")
```

#### Capture Region

```python
path = await screenshot.capture_region(0, 0, 1920, 1080)
```

### Macros

#### Record a Macro

```python
macros = copilot.get_module('macros')

# Start recording
macros.start_recording()

# Perform actions...
await keyboard.type_text("print('hello')")
await keyboard.press_key("Return", set())

# Stop and save
macro = macros.stop_recording("my_macro")

# Replay
await macros.replay_macro("my_macro", speed=2.0)
```

### AI Integration

#### Enable AI Model

```python
ai = copilot.get_module('ai')

# Load LLaMA model
config = {
    'type': 'llama2',
    'model_path': '/path/to/model.gguf',
    'context_length': 2048
}
model_id = ai.load_model(config)
ai.set_active_model(model_id)
```

#### Get AI Suggestions

```python
# Get window arrangement suggestion
context = "I have Firefox, VSCode, and Terminal open"
suggestions = ai.get_suggestions(context)

for suggestion in suggestions:
    print(f"Suggestion: {suggestion}")
```

#### Generate Macro from Description

```python
description = "Open Firefox, navigate to github.com, and maximize window"
macro_steps = ai.generate_macro(description)

for step in macro_steps:
    print(f"Step: {step}")
```

## Using the Dashboard

### Plugin Management

1. **Load a Plugin**:
   - Click "Load Plugin" button
   - Browse to `.so` file
   - Select capabilities to grant
   - Click "Load"

2. **Enable/Disable Plugin**:
   - Select plugin from list
   - Click checkbox to enable/disable

3. **Unload Plugin**:
   - Select plugin
   - Click "Unload Plugin"

### AI Model Selection

1. Click the AI Model dropdown
2. Select from available models:
   - LLaMA
   - LLaMA2
   - GPT-3.5
   - GPT-4
   - Custom models

3. Click "Configure" to set model parameters:
   - Temperature
   - Max tokens
   - Context length
   - GPU acceleration

### Quick Actions

**Screenshot**: Capture screen immediately

**Window Arrangement**: Arrange windows with AI

**Macro Recording**: Start/stop macro recording

### System Status

Monitor in real-time:
- CPU usage
- Memory usage
- Active windows count
- Pending events
- Current AI model

## Hotkeys (Default)

- `Super+A`: AI-powered window arrangement
- `Super+S`: Take screenshot
- `Super+R`: Start macro recording
- `Super+P`: Stop macro recording
- `Super+D`: Show/hide dashboard

Configure hotkeys in: `~/.config/copilot/config.yaml`

## Configuration

### Main Config File

Located at: `~/.config/copilot/config.yaml`

```yaml
# Core settings
core:
  worker_threads: 8
  event_queue_size: 10000
  log_level: info

# Window manager
window_manager:
  display_protocol: auto  # auto, x11, wayland
  cache_timeout_ms: 100

# AI settings
ai:
  default_model: llama2
  auto_suggestions: true
  context_length: 2048

# Hotkeys
hotkeys:
  arrange_windows: Super+A
  screenshot: Super+S
  record_macro: Super+R
  dashboard: Super+D

# UI
ui:
  theme: dark
  animations: true
  tray_icon: true
  startup_minimize: false

# Plugins
plugins:
  auto_load:
    - ai_window_arranger
    - productivity_macros
  search_paths:
    - ~/.local/share/copilot/plugins
    - /usr/share/copilot/plugins
```

## Plugin Development

### Create a Simple Plugin

```cpp
#include "plugin_manager.hpp"

class MyPlugin : public copilot::core::PluginBase {
public:
    PluginMetadata get_metadata() const override {
        PluginMetadata meta;
        meta.name = "My Plugin";
        meta.version = "1.0.0";
        meta.author = "Your Name";
        meta.description = "Description of my plugin";
        meta.capabilities_flags = CAPABILITY_WINDOW_ACCESS;
        return meta;
    }

    bool initialize(PluginAPI* api) override {
        api_ = api;

        // Subscribe to events
        auto sub_id = api->subscribe_event("window.focused",
            [this](const void* data) {
                this->on_window_focused(data);
            });

        api->log_info("My Plugin initialized");
        return true;
    }

    void shutdown() override {
        api_->log_info("My Plugin shutdown");
    }

private:
    void on_window_focused(const void* data) {
        api_->log_info("Window focused!");
    }

    PluginAPI* api_;
};

COPILOT_PLUGIN_ENTRY(MyPlugin)
```

### Build Plugin

```bash
g++ -shared -fPIC -o my_plugin.so my_plugin.cpp \
    -I/usr/include/copilot \
    -L/usr/lib -lcopilot_core
```

### Load Plugin

```bash
copilot-cli plugin load ~/.local/share/copilot/plugins/my_plugin.so
```

Or via UI: Dashboard → Load Plugin

## Troubleshooting

### UI doesn't start

Check Qt6 installation:
```bash
qmake --version
```

Install if missing:
```bash
sudo dnf install qt6-qtbase  # Fedora
sudo apt install qt6-base-dev  # Ubuntu
```

### Wayland support issues

Install Wayland tools:
```bash
sudo dnf install grim slurp wl-clipboard ydotool
```

Set environment variable:
```bash
export COPILOT_DISPLAY_PROTOCOL=wayland
```

### Permission denied errors

Grant necessary permissions:
```bash
sudo usermod -aG input $USER
```

Logout and login again.

### AI model not loading

Check model path in config:
```yaml
ai:
  models:
    llama2:
      path: /path/to/model.gguf
```

Ensure model file exists and is readable.

## Next Steps

- Read [Architecture Documentation](ARCHITECTURE.md)
- Explore [Plugin API](API.md#plugin-api)
- Check [Example Plugins](../src/plugins/examples/)
- Join community discussions

## Getting Help

- Documentation: `~/.local/share/doc/copilot/`
- Issues: https://github.com/yourusername/linux-copilot/issues
- Discussions: https://github.com/yourusername/linux-copilot/discussions
- Email: support@linux-copilot.org
