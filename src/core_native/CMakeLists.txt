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

# Source files (only add files that exist)
set(CORE_SOURCES "")

# Check for each source file and add if it exists
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src/event_loop.cpp")
    list(APPEND CORE_SOURCES src/event_loop.cpp)
endif()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src/thread_pool.cpp")
    list(APPEND CORE_SOURCES src/thread_pool.cpp)
endif()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src/plugin_manager.cpp")
    list(APPEND CORE_SOURCES src/plugin_manager.cpp)
endif()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src/ipc_bridge.cpp")
    list(APPEND CORE_SOURCES src/ipc_bridge.cpp)
endif()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src/security_manager.cpp")
    list(APPEND CORE_SOURCES src/security_manager.cpp)
endif()

if(X11_FOUND AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src/window_manager_native.cpp")
    list(APPEND CORE_SOURCES src/window_manager_native.cpp)
endif()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src/input_manager_native.cpp")
    list(APPEND CORE_SOURCES src/input_manager_native.cpp)
endif()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src/screenshot_native.cpp")
    list(APPEND CORE_SOURCES src/screenshot_native.cpp)
endif()

# Only create library if we have at least one source file
if(CORE_SOURCES)
    add_library(copilot_core SHARED ${CORE_SOURCES})
else()
    message(FATAL_ERROR "No source files found for copilot_core library!")
endif()

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
if(pybind11_FOUND AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/bindings/python_bindings.cpp")
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

# Example plugins (if directory exists)
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/examples")
    add_subdirectory(examples)
endif()

# Tests (if enabled and directory exists)
if(BUILD_TESTING AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/tests")
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
