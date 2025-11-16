/**
 * @file window_manager_x11.hpp
 * @brief High-performance X11 window management
 */

#ifndef COPILOT_WINDOW_MANAGER_X11_HPP
#define COPILOT_WINDOW_MANAGER_X11_HPP

#include <string>
#include <vector>
#include <memory>
#include <functional>

#ifdef HAVE_X11
#include <X11/Xlib.h>
#include <X11/Xatom.h>
#include <X11/extensions/XTest.h>
#include <X11/extensions/Xrandr.h>
#endif

namespace copilot {
namespace modules {

/**
 * @brief Window information
 */
struct WindowInfo {
    uint64_t window_id;
    std::string title;
    std::string wm_class;
    std::string wm_name;
    int x, y;
    int width, height;
    int desktop;
    bool is_visible;
    bool is_focused;
    bool is_minimized;
    bool is_maximized;
    uint32_t pid;
};

/**
 * @brief Desktop information
 */
struct DesktopInfo {
    int index;
    std::string name;
    int width, height;
    bool is_current;
};

/**
 * @brief Window event types
 */
enum class WindowEventType {
    CREATED,
    DESTROYED,
    FOCUSED,
    UNFOCUSED,
    MOVED,
    RESIZED,
    MINIMIZED,
    MAXIMIZED,
    DESKTOP_CHANGED,
    TITLE_CHANGED,
    CLASS_CHANGED
};

/**
 * @brief Window event callback
 */
using WindowEventCallback = std::function<void(WindowEventType, const WindowInfo&)>;

/**
 * @brief High-performance X11 window manager
 */
class WindowManagerX11 {
public:
    WindowManagerX11();
    ~WindowManagerX11();

    // Disable copy/move
    WindowManagerX11(const WindowManagerX11&) = delete;
    WindowManagerX11& operator=(const WindowManagerX11&) = delete;

    /**
     * @brief Initialize window manager
     */
    bool initialize();

    /**
     * @brief Shutdown window manager
     */
    void shutdown();

    /**
     * @brief Check if initialized
     */
    bool is_initialized() const { return initialized_; }

    // Window queries
    /**
     * @brief Get all windows
     */
    std::vector<WindowInfo> get_all_windows() const;

    /**
     * @brief Get active window
     */
    WindowInfo get_active_window() const;

    /**
     * @brief Get window by ID
     */
    WindowInfo get_window_by_id(uint64_t window_id) const;

    /**
     * @brief Find windows by title
     */
    std::vector<WindowInfo> find_windows_by_title(const std::string& title) const;

    /**
     * @brief Find windows by class
     */
    std::vector<WindowInfo> find_windows_by_class(const std::string& wm_class) const;

    /**
     * @brief Find windows by PID
     */
    std::vector<WindowInfo> find_windows_by_pid(uint32_t pid) const;

    // Window manipulation
    /**
     * @brief Activate (focus) a window
     */
    bool activate_window(uint64_t window_id);

    /**
     * @brief Move window
     */
    bool move_window(uint64_t window_id, int x, int y);

    /**
     * @brief Resize window
     */
    bool resize_window(uint64_t window_id, int width, int height);

    /**
     * @brief Move and resize window
     */
    bool set_window_geometry(uint64_t window_id, int x, int y, int width, int height);

    /**
     * @brief Minimize window
     */
    bool minimize_window(uint64_t window_id);

    /**
     * @brief Maximize window
     */
    bool maximize_window(uint64_t window_id);

    /**
     * @brief Unmaximize window
     */
    bool unmaximize_window(uint64_t window_id);

    /**
     * @brief Close window
     */
    bool close_window(uint64_t window_id);

    /**
     * @brief Move window to desktop
     */
    bool move_window_to_desktop(uint64_t window_id, int desktop);

    // Desktop management
    /**
     * @brief Get desktop count
     */
    int get_desktop_count() const;

    /**
     * @brief Get current desktop
     */
    int get_current_desktop() const;

    /**
     * @brief Switch to desktop
     */
    bool switch_to_desktop(int desktop);

    /**
     * @brief Get desktop information
     */
    std::vector<DesktopInfo> get_desktops() const;

    // Event monitoring
    /**
     * @brief Start monitoring window events
     */
    bool start_event_monitoring();

    /**
     * @brief Stop monitoring window events
     */
    void stop_event_monitoring();

    /**
     * @brief Register event callback
     */
    void register_event_callback(WindowEventCallback callback);

    // Advanced features
    /**
     * @brief Arrange windows in grid layout
     */
    bool arrange_windows_grid(const std::vector<uint64_t>& window_ids,
                             int rows, int columns);

    /**
     * @brief Arrange windows in tile layout
     */
    bool arrange_windows_tile(const std::vector<uint64_t>& window_ids);

    /**
     * @brief Get screen geometry
     */
    struct ScreenGeometry {
        int x, y;
        int width, height;
    };
    std::vector<ScreenGeometry> get_screen_geometries() const;

private:
#ifdef HAVE_X11
    // X11 display connection
    Display* display_;

    // Root window
    Window root_;

    // Screen number
    int screen_;

    // Atoms for EWMH
    struct {
        Atom active_window;
        Atom client_list;
        Atom current_desktop;
        Atom desktop_count;
        Atom desktop_names;
        Atom window_name;
        Atom window_class;
        Atom window_desktop;
        Atom window_state;
        Atom window_state_maximized_horz;
        Atom window_state_maximized_vert;
        Atom window_state_hidden;
        Atom close_window;
    } atoms_;

    // Initialize atoms
    void init_atoms();

    // Get window property
    bool get_window_property(Window window, Atom property,
                            Atom type, unsigned char** data,
                            unsigned long* nitems) const;

    // Set window property
    bool set_window_property(Window window, Atom property,
                            Atom type, const void* data,
                            int nelements) const;

    // Send client message
    bool send_client_message(Window window, Atom message_type,
                           long data0, long data1 = 0,
                           long data2 = 0, long data3 = 0,
                           long data4 = 0) const;

    // Get window info
    WindowInfo get_window_info_internal(Window window) const;

    // Event monitoring thread
    void event_monitoring_thread();
    std::unique_ptr<std::thread> event_thread_;
    std::atomic<bool> monitoring_active_;

    // Event callbacks
    std::vector<WindowEventCallback> event_callbacks_;
    mutable std::mutex callbacks_mutex_;

    // Cache for window list
    mutable std::vector<WindowInfo> window_cache_;
    mutable std::mutex cache_mutex_;
    mutable std::chrono::steady_clock::time_point cache_timestamp_;
#endif

    bool initialized_;
};

} // namespace modules
} // namespace copilot

#endif // COPILOT_WINDOW_MANAGER_X11_HPP
