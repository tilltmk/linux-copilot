#!/bin/bash
#
# Installation script for Linux Agentic Copilot
# Installs system dependencies and Python package
#

set -e

echo "==================================="
echo "Linux Agentic Copilot - Installer"
echo "==================================="
echo ""

# Detect distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    echo "Cannot detect Linux distribution"
    exit 1
fi

echo "Detected distribution: $DISTRO"
echo ""

# Install system dependencies based on distribution
echo "Installing system dependencies..."

case $DISTRO in
    ubuntu|debian)
        sudo apt-get update
        echo "Installing X11 tools..."
        sudo apt-get install -y \
            xdotool \
            wmctrl \
            scrot \
            maim \
            slop \
            imagemagick \
            ffmpeg

        echo "Installing Python development packages..."
        sudo apt-get install -y \
            python3 \
            python3-pip \
            python3-venv \
            python3-dev

        # Optional: Wayland tools
        read -p "Install Wayland support? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo apt-get install -y \
                grim \
                slurp \
                wf-recorder \
                ydotool
        fi
        ;;

    fedora|rhel|centos)
        sudo dnf install -y \
            xdotool \
            wmctrl \
            scrot \
            ImageMagick \
            ffmpeg

        sudo dnf install -y \
            python3 \
            python3-pip \
            python3-devel

        # Optional: Wayland tools
        read -p "Install Wayland support? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo dnf install -y \
                grim \
                slurp \
                wf-recorder \
                ydotool
        fi
        ;;

    arch|manjaro)
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

        # Optional: Wayland tools
        read -p "Install Wayland support? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo pacman -S --needed \
                grim \
                slurp \
                wf-recorder \
                ydotool
        fi
        ;;

    *)
        echo "Unsupported distribution: $DISTRO"
        echo "Please install the following packages manually:"
        echo "  - xdotool, wmctrl, scrot/maim, ImageMagick, ffmpeg"
        echo "  - python3, python3-pip"
        echo "  - (Optional) grim, slurp, wf-recorder, ydotool for Wayland"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        ;;
esac

echo ""
echo "System dependencies installed successfully"
echo ""

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install package in development mode
echo "Installing linux-copilot package..."
pip install -e .

echo ""
echo "==================================="
echo "Installation completed successfully!"
echo "==================================="
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To start the copilot, run:"
echo "  python -m src.copilot"
echo ""
echo "For more information, see the documentation in docs/"
echo ""
