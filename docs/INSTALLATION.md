# Installation Guide - Linux Agentic Copilot

Complete installation guide for Linux Agentic Copilot on various Linux distributions.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Automatic Installation](#automatic-installation)
3. [Manual Installation](#manual-installation)
4. [Wayland Support](#wayland-support)
5. [Post-Installation](#post-installation)
6. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **OS**: Linux (kernel 4.0+)
- **Python**: 3.8 or higher
- **RAM**: 512 MB
- **Display Server**: X11 or Wayland

### Supported Distributions
- Ubuntu 20.04+
- Debian 11+
- Fedora 35+
- Arch Linux
- openSUSE
- Other systemd-based distributions

---

## Automatic Installation

The easiest way to install Linux Copilot is using the automatic installer:

```bash
# Clone the repository
git clone https://github.com/yourusername/linux-copilot.git
cd linux-copilot

# Run the installer
./install.sh
```

The installer will:
1. Detect your Linux distribution
2. Install all required system packages
3. Set up a Python virtual environment
4. Install Python dependencies
5. Install the linux-copilot package

---

## Manual Installation

### Step 1: Install System Dependencies

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y \
    xdotool \
    wmctrl \
    scrot \
    maim \
    slop \
    imagemagick \
    ffmpeg \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev
```

#### Fedora/RHEL/CentOS

```bash
sudo dnf install -y \
    xdotool \
    wmctrl \
    scrot \
    ImageMagick \
    ffmpeg \
    python3 \
    python3-pip \
    python3-devel
```

#### Arch Linux

```bash
sudo pacman -Syu --needed \
    xdotool \
    wmctrl \
    scrot \
    maim \
    slop \
    imagemagick \
    ffmpeg \
    python \
    python-pip
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Step 3: Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

---

## Wayland Support

For Wayland users, additional tools are required:

### Ubuntu/Debian

```bash
sudo apt-get install -y \
    grim \
    slurp \
    wf-recorder \
    ydotool
```

### Fedora/RHEL

```bash
sudo dnf install -y \
    grim \
    slurp \
    wf-recorder \
    ydotool
```

### Arch Linux

```bash
sudo pacman -S --needed \
    grim \
    slurp \
    wf-recorder \
    ydotool
```

### Configure ydotool

For input simulation on Wayland:

```bash
# Start ydotool daemon
sudo systemctl enable ydotool
sudo systemctl start ydotool

# Add your user to input group
sudo usermod -a -G input $USER

# Logout and login again for changes to take effect
```

---

## Post-Installation

### Verify Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Check installation
python -c "import src.copilot; print('Installation successful!')"
```

### Create Configuration

```bash
# Create config directory
mkdir -p ~/.config/linux-copilot

# Copy default configuration
cp config/default_config.json ~/.config/linux-copilot/config.json

# Edit configuration as needed
nano ~/.config/linux-copilot/config.json
```

### Test Basic Functionality

```bash
# Run tests
cd tests
./run_tests.sh
```

---

## Troubleshooting

### Common Issues

#### 1. Permission Denied for Input Devices

**Problem**: Cannot access keyboard/mouse events

**Solution**:
```bash
# Add user to input group
sudo usermod -a -G input $USER

# Logout and login again
```

#### 2. Wayland Tools Not Found

**Problem**: `grim`, `slurp`, or `ydotool` not found

**Solution**:
```bash
# Check session type
echo $XDG_SESSION_TYPE

# If Wayland, install Wayland tools (see Wayland Support section)
```

#### 3. Python Import Errors

**Problem**: Module not found errors

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
pip install -e .
```

#### 4. X11 Tools Not Working

**Problem**: `xdotool` or `wmctrl` commands fail

**Solution**:
```bash
# Verify DISPLAY variable
echo $DISPLAY

# Check if X11 is running
ps aux | grep X

# Test xdotool manually
xdotool getactivewindow
```

### Getting Help

- **Documentation**: Check the `docs/` directory
- **Issues**: Report bugs on GitHub Issues
- **Community**: Join our discussion forum

---

## Next Steps

After installation:

1. Read the [User Guide](USER_GUIDE.md)
2. Review [API Documentation](API.md)
3. Try [Example Plugins](../src/plugins/examples/)
4. Create your own automations!

---

## Uninstallation

To remove Linux Copilot:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv/

# Remove configuration
rm -rf ~/.config/linux-copilot/

# Remove logs
rm -rf ~/.local/share/linux-copilot/

# Optionally remove system packages (be careful!)
# sudo apt-get remove xdotool wmctrl scrot maim ...
```
