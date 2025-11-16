cmake_minimum_required(VERSION 3.16)
project(LinuxCopilot VERSION 1.0.0 LANGUAGES CXX)

# Project-wide settings
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Build options
option(BUILD_UI "Build Qt6 UI" ON)
option(BUILD_PYTHON_BINDINGS "Build Python bindings" ON)
option(BUILD_TESTS "Build test suite" ON)
option(BUILD_DOCS "Build documentation" ON)
option(ENABLE_X11 "Enable X11 support" ON)
option(ENABLE_WAYLAND "Enable Wayland support" ON)
option(ENABLE_AI "Enable AI integration" ON)

# Performance optimization flags
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -flto -DNDEBUG")
    set(CMAKE_INTERPROCEDURAL_OPTIMIZATION ON)
endif()

if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    set(CMAKE_CXX_FLAGS_DEBUG "-O0 -g -fsanitize=address -fsanitize=undefined")
endif()

# Find required packages
find_package(Threads REQUIRED)
find_package(PkgConfig REQUIRED)

# Qt6 (for UI)
if(BUILD_UI)
    find_package(Qt6 COMPONENTS Core Widgets Gui Network QUIET)
    if(NOT Qt6_FOUND)
        message(WARNING "Qt6 not found. Disabling UI build.")
        set(BUILD_UI OFF)
    else()
        set(CMAKE_AUTOMOC ON)
        set(CMAKE_AUTORCC ON)
        set(CMAKE_AUTOUIC ON)
        message(STATUS "Qt6 found. UI will be built.")
    endif()
endif()

# Python (for bindings)
if(BUILD_PYTHON_BINDINGS)
    find_package(Python3 COMPONENTS Interpreter Development QUIET)
    if(NOT Python3_FOUND)
        message(WARNING "Python3 development files not found. Disabling Python bindings.")
        set(BUILD_PYTHON_BINDINGS OFF)
    else()
        find_package(pybind11 CONFIG QUIET)
        if(NOT pybind11_FOUND)
            message(WARNING "pybind11 not found. Disabling Python bindings.")
            set(BUILD_PYTHON_BINDINGS OFF)
        endif()
    endif()
endif()

# X11
if(ENABLE_X11)
    pkg_check_modules(X11 x11 xrandr xi xtst)
    if(X11_FOUND)
        add_definitions(-DHAVE_X11)
        message(STATUS "X11 support enabled")
    else()
        message(WARNING "X11 libraries not found. Disabling X11 support.")
        set(ENABLE_X11 OFF)
    endif()
endif()

# Wayland
if(ENABLE_WAYLAND)
    pkg_check_modules(WAYLAND wayland-client)
    if(WAYLAND_FOUND)
        add_definitions(-DHAVE_WAYLAND)
    endif()
endif()

# llama.cpp (for AI)
if(ENABLE_AI)
    find_library(LLAMA_LIB llama PATHS /usr/local/lib /usr/lib)
    if(LLAMA_LIB)
        add_definitions(-DHAVE_LLAMA)
    endif()
endif()

# Installation directories
include(GNUInstallDirs)
set(COPILOT_INSTALL_BINDIR ${CMAKE_INSTALL_BINDIR})
set(COPILOT_INSTALL_LIBDIR ${CMAKE_INSTALL_LIBDIR})
set(COPILOT_INSTALL_INCLUDEDIR ${CMAKE_INSTALL_INCLUDEDIR}/copilot)
set(COPILOT_INSTALL_DATADIR ${CMAKE_INSTALL_DATADIR}/copilot)
set(COPILOT_INSTALL_DOCDIR ${CMAKE_INSTALL_DOCDIR})

# Subdirectories (only add if they exist)
if(EXISTS "${CMAKE_SOURCE_DIR}/src/core_native/CMakeLists.txt")
    add_subdirectory(src/core_native)
else()
    message(WARNING "src/core_native/CMakeLists.txt not found. Skipping core build.")
endif()

if(BUILD_UI AND EXISTS "${CMAKE_SOURCE_DIR}/src/ui_qt6/CMakeLists.txt")
    add_subdirectory(src/ui_qt6)
endif()

if(ENABLE_AI AND EXISTS "${CMAKE_SOURCE_DIR}/src/ai_integration/CMakeLists.txt")
    add_subdirectory(src/ai_integration)
endif()

if(EXISTS "${CMAKE_SOURCE_DIR}/src/modules_native/CMakeLists.txt")
    add_subdirectory(src/modules_native)
endif()

if(BUILD_PYTHON_BINDINGS AND pybind11_FOUND AND EXISTS "${CMAKE_SOURCE_DIR}/src/bindings/CMakeLists.txt")
    add_subdirectory(src/bindings)
endif()

if(BUILD_TESTS AND EXISTS "${CMAKE_SOURCE_DIR}/tests/CMakeLists.txt")
    enable_testing()
    add_subdirectory(tests)
endif()

if(BUILD_DOCS AND EXISTS "${CMAKE_SOURCE_DIR}/docs/CMakeLists.txt")
    find_package(Doxygen)
    if(DOXYGEN_FOUND)
        add_subdirectory(docs)
    endif()
endif()

# Install Python files
install(DIRECTORY src/
    DESTINATION ${COPILOT_INSTALL_DATADIR}/python
    FILES_MATCHING PATTERN "*.py"
)

# Install configuration files
install(DIRECTORY config/
    DESTINATION ${CMAKE_INSTALL_SYSCONFDIR}/copilot
    FILES_MATCHING PATTERN "*.conf" PATTERN "*.yaml"
)

# Install desktop file and icon
install(FILES resources/copilot.desktop
    DESTINATION ${CMAKE_INSTALL_DATADIR}/applications
)

install(FILES resources/copilot.svg
    DESTINATION ${CMAKE_INSTALL_DATADIR}/icons/hicolor/scalable/apps
)

# CPack configuration for packaging
set(CPACK_PACKAGE_NAME "linux-copilot")
set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "High-performance visual automation framework for Linux")
set(CPACK_PACKAGE_VENDOR "Linux Copilot Project")
set(CPACK_PACKAGE_CONTACT "support@linux-copilot.org")

# DEB package
set(CPACK_DEBIAN_PACKAGE_DEPENDS "libqt6core6, libqt6widgets6, libqt6gui6, libx11-6, python3")
set(CPACK_DEBIAN_PACKAGE_SECTION "utils")

# RPM package
set(CPACK_RPM_PACKAGE_REQUIRES "qt6-qtbase >= 6.2, libX11, python3")
set(CPACK_RPM_PACKAGE_GROUP "Applications/System")

# Generators
set(CPACK_GENERATOR "DEB;RPM;TGZ")

include(CPack)

# Print configuration summary
message(STATUS "")
message(STATUS "Linux Copilot Configuration Summary:")
message(STATUS "  Version: ${PROJECT_VERSION}")
message(STATUS "  Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  C++ compiler: ${CMAKE_CXX_COMPILER}")
message(STATUS "  Install prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "")
message(STATUS "Features:")
message(STATUS "  Qt6 UI: ${BUILD_UI}")
message(STATUS "  Python bindings: ${BUILD_PYTHON_BINDINGS}")
message(STATUS "  X11 support: ${ENABLE_X11}")
message(STATUS "  Wayland support: ${ENABLE_WAYLAND}")
message(STATUS "  AI integration: ${ENABLE_AI}")
message(STATUS "  Tests: ${BUILD_TESTS}")
message(STATUS "  Documentation: ${BUILD_DOCS}")
message(STATUS "")
