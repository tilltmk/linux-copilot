cmake_minimum_required(VERSION 3.16)
project(copilot_core VERSION 1.0.0 LANGUAGES CXX)

# C++ Standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler flags for performance
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -flto -DNDEBUG")
set(CMAKE_CXX_FLAGS_DEBUG "-O0 -g -fsanitize=address -fsanitize=undefined")

# Find required packages
find_package(Threads REQUIRED)
find_package(PkgConfig REQUIRED)

# Optional: X11 support
pkg_check_modules(X11 x11 xrandr xi xtst)
if(X11_FOUND)
    add_definitions(-DHAVE_X11)
endif()

# Optional: Wayland support
pkg_check_modules(WAYLAND wayland-client)
if(WAYLAND_FOUND)
    add_definitions(-DHAVE_WAYLAND)
endif()

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${X11_INCLUDE_DIRS}
    ${WAYLAND_INCLUDE_DIRS}
)

# Source files
set(CORE_SOURCES
    src/event_loop.cpp
    src/plugin_manager.cpp
    src/ipc_bridge.cpp
    src/thread_pool.cpp
    src/security_manager.cpp
    src/window_manager_native.cpp
    src/input_manager_native.cpp
    src/screenshot_native.cpp
)

# Core library
add_library(copilot_core SHARED ${CORE_SOURCES})

target_link_libraries(copilot_core
    PUBLIC
        Threads::Threads
        ${CMAKE_DL_LIBS}
        ${X11_LIBRARIES}
        ${WAYLAND_LIBRARIES}
)

# Set RPATH for plugin loading
set_target_properties(copilot_core PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION 1
    INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib"
    BUILD_RPATH "${CMAKE_BINARY_DIR}"
)

# Python bindings (using pybind11)
find_package(pybind11 CONFIG)
if(pybind11_FOUND)
    pybind11_add_module(copilot_native bindings/python_bindings.cpp)
    target_link_libraries(copilot_native PRIVATE copilot_core)
endif()

# Install targets
install(TARGETS copilot_core
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)

install(DIRECTORY include/
    DESTINATION include/copilot
    FILES_MATCHING PATTERN "*.hpp"
)

# Example plugins
add_subdirectory(examples)

# Tests
if(BUILD_TESTING)
    enable_testing()
    add_subdirectory(tests)
endif()

# Documentation
find_package(Doxygen)
if(DOXYGEN_FOUND)
    set(DOXYGEN_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/docs)
    set(DOXYGEN_GENERATE_HTML YES)
    set(DOXYGEN_GENERATE_MAN YES)

    doxygen_add_docs(docs
        ${CMAKE_CURRENT_SOURCE_DIR}/include
        COMMENT "Generating API documentation"
    )
endif()
