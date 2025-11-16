#!/bin/bash
# Advanced installation script for Linux Copilot
# Supports Fedora, OpenSUSE, Debian, Ubuntu, Arch
# Auto-detects distribution and installs dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_msg() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

print_msg "$BLUE" "╔════════════════════════════════════════════════════════════╗"
print_msg "$BLUE" "║       Linux Copilot - Advanced Installation Script        ║"
print_msg "$BLUE" "║    High-Performance Visual Automation Framework v1.0      ║"
print_msg "$BLUE" "╚════════════════════════════════════════════════════════════╝"
echo ""

# Detect distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        DISTRO_VERSION=$VERSION_ID
    else
        print_msg "$RED" "Error: Cannot detect distribution"
        exit 1
    fi

    print_msg "$GREEN" "Detected: $PRETTY_NAME"
}

# Check if running as root for system install
check_root() {
    if [ "$EUID" -eq 0 ]; then
        INSTALL_PREFIX="/usr"
        SYSTEM_INSTALL=true
        print_msg "$YELLOW" "Running as root - System-wide installation"
    else
        INSTALL_PREFIX="$HOME/.local"
        SYSTEM_INSTALL=false
        print_msg "$YELLOW" "Running as user - Local installation to $INSTALL_PREFIX"
    fi
}

# Install dependencies based on distro
install_dependencies() {
    print_msg "$BLUE" "\n[1/6] Installing dependencies..."

    case $DISTRO in
        fedora)
            print_msg "$GREEN" "Installing for Fedora..."
            if [ "$SYSTEM_INSTALL" = true ]; then
                dnf install -y \
                    gcc-c++ cmake ninja-build \
                    qt6-qtbase-devel qt6-qtbase-gui \
                    python3-devel python3-pip \
                    libX11-devel libXi-devel libXtst-devel libXrandr-devel \
                    wayland-devel \
                    doxygen graphviz \
                    xdotool wmctrl scrot \
                    grim slurp wl-clipboard ydotool
            else
                print_msg "$YELLOW" "Please install dependencies manually:"
                print_msg "$YELLOW" "sudo dnf install gcc-c++ cmake ninja-build qt6-qtbase-devel ..."
            fi
            ;;

        opensuse*|suse)
            print_msg "$GREEN" "Installing for openSUSE..."
            if [ "$SYSTEM_INSTALL" = true ]; then
                zypper install -y \
                    gcc-c++ cmake ninja \
                    qt6-base-devel \
                    python3-devel python3-pip \
                    libX11-devel libXi-devel libXtst-devel libXrandr-devel \
                    wayland-devel \
                    doxygen graphviz \
                    xdotool wmctrl scrot \
                    grim slurp wl-clipboard ydotool
            else
                print_msg "$YELLOW" "Please install dependencies manually:"
                print_msg "$YELLOW" "sudo zypper install gcc-c++ cmake ninja qt6-base-devel ..."
            fi
            ;;

        debian|ubuntu)
            print_msg "$GREEN" "Installing for Debian/Ubuntu..."
            if [ "$SYSTEM_INSTALL" = true ]; then
                apt-get update
                apt-get install -y \
                    build-essential cmake ninja-build \
                    qt6-base-dev libqt6gui6 \
                    python3-dev python3-pip \
                    libx11-dev libxi-dev libxtst-dev libxrandr-dev \
                    libwayland-dev \
                    doxygen graphviz \
                    xdotool wmctrl scrot maim \
                    grim slurp wl-clipboard ydotool
            else
                print_msg "$YELLOW" "Please install dependencies manually:"
                print_msg "$YELLOW" "sudo apt install build-essential cmake ninja-build qt6-base-dev ..."
            fi
            ;;

        arch|manjaro)
            print_msg "$GREEN" "Installing for Arch Linux..."
            if [ "$SYSTEM_INSTALL" = true ]; then
                pacman -Syu --noconfirm \
                    base-devel cmake ninja \
                    qt6-base \
                    python python-pip \
                    libx11 libxi libxtst libxrandr \
                    wayland \
                    doxygen graphviz \
                    xdotool wmctrl scrot \
                    grim slurp wl-clipboard ydotool
            else
                print_msg "$YELLOW" "Please install dependencies manually:"
                print_msg "$YELLOW" "sudo pacman -S base-devel cmake ninja qt6-base ..."
            fi
            ;;

        *)
            print_msg "$RED" "Unsupported distribution: $DISTRO"
            print_msg "$YELLOW" "Please install dependencies manually and run: ./build.sh"
            exit 1
            ;;
    esac
}

# Install Python dependencies
install_python_deps() {
    print_msg "$BLUE" "\n[2/6] Installing Python dependencies..."

    if [ "$SYSTEM_INSTALL" = true ]; then
        pip3 install --upgrade \
            pybind11 \
            asyncio-mqtt \
            pydantic \
            python-daemon \
            python-xlib \
            pytest pytest-asyncio \
            black flake8 mypy
    else
        pip3 install --user --upgrade \
            pybind11 \
            asyncio-mqtt \
            pydantic \
            python-daemon \
            python-xlib \
            pytest pytest-asyncio \
            black flake8 mypy
    fi
}

# Build C++ core
build_core() {
    print_msg "$BLUE" "\n[3/6] Building C++ core..."

    mkdir -p build
    cd build

    cmake .. \
        -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX" \
        -DBUILD_UI=ON \
        -DBUILD_PYTHON_BINDINGS=ON \
        -DBUILD_TESTS=ON \
        -DENABLE_X11=ON \
        -DENABLE_WAYLAND=ON \
        -DENABLE_AI=ON

    ninja -j$(nproc)

    cd ..
}

# Run tests
run_tests() {
    print_msg "$BLUE" "\n[4/6] Running tests..."

    cd build
    ctest --output-on-failure
    cd ..

    # Python tests
    cd tests
    pytest -v
    cd ..
}

# Install
install_copilot() {
    print_msg "$BLUE" "\n[5/6] Installing Linux Copilot..."

    cd build

    if [ "$SYSTEM_INSTALL" = true ]; then
        ninja install
    else
        DESTDIR="$INSTALL_PREFIX" ninja install
    fi

    cd ..

    # Create virtual environment for Python components
    if [ "$SYSTEM_INSTALL" = false ]; then
        python3 -m venv venv
        source venv/bin/activate
        pip install -e .
    fi
}

# Post-install configuration
post_install() {
    print_msg "$BLUE" "\n[6/6] Post-installation setup..."

    # Create config directory
    mkdir -p "$HOME/.config/copilot"

    # Copy default config if not exists
    if [ ! -f "$HOME/.config/copilot/config.yaml" ]; then
        cp config/default.yaml "$HOME/.config/copilot/config.yaml"
    fi

    # Create plugins directory
    mkdir -p "$HOME/.local/share/copilot/plugins"

    # Set up systemd service for user (optional)
    if [ "$SYSTEM_INSTALL" = false ]; then
        mkdir -p "$HOME/.config/systemd/user"
        cat > "$HOME/.config/systemd/user/copilot.service" <<EOF
[Unit]
Description=Linux Copilot Service
After=graphical-session.target

[Service]
Type=simple
ExecStart=$INSTALL_PREFIX/bin/copilot --daemon
Restart=on-failure

[Install]
WantedBy=default.target
EOF

        print_msg "$YELLOW" "Systemd service created. Enable with:"
        print_msg "$YELLOW" "  systemctl --user enable copilot.service"
        print_msg "$YELLOW" "  systemctl --user start copilot.service"
    fi
}

# Main installation flow
main() {
    detect_distro
    check_root

    print_msg "$YELLOW" "\nThis script will:"
    print_msg "$YELLOW" "  1. Install system dependencies"
    print_msg "$YELLOW" "  2. Install Python dependencies"
    print_msg "$YELLOW" "  3. Build C++ core with optimizations"
    print_msg "$YELLOW" "  4. Run test suite"
    print_msg "$YELLOW" "  5. Install to $INSTALL_PREFIX"
    print_msg "$YELLOW" "  6. Configure environment"
    echo ""
    read -p "Continue? (y/N) " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_msg "$RED" "Installation cancelled"
        exit 1
    fi

    install_dependencies
    install_python_deps
    build_core

    # Optional: Skip tests
    read -p "Run tests? (Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        run_tests
    fi

    install_copilot
    post_install

    print_msg "$GREEN" "\n╔════════════════════════════════════════════════════════════╗"
    print_msg "$GREEN" "║          Installation completed successfully!             ║"
    print_msg "$GREEN" "╚════════════════════════════════════════════════════════════╝"
    echo ""
    print_msg "$BLUE" "Next steps:"
    print_msg "$BLUE" "  1. Run: copilot-ui (to start the GUI)"
    print_msg "$BLUE" "  2. Run: copilot-cli (for command-line interface)"
    print_msg "$BLUE" "  3. Check docs: $INSTALL_PREFIX/share/doc/copilot/"
    echo ""
    print_msg "$YELLOW" "Configuration: $HOME/.config/copilot/config.yaml"
    print_msg "$YELLOW" "Plugins: $HOME/.local/share/copilot/plugins/"
    echo ""
}

main "$@"
