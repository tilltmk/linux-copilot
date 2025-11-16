/**
 * @file plugin_manager.hpp
 * @brief Dynamic plugin loading and management system
 *
 * Provides secure, sandboxed plugin loading with hot-reloading support.
 * Plugins can be loaded/unloaded at runtime without restarting the application.
 */

#ifndef COPILOT_PLUGIN_MANAGER_HPP
#define COPILOT_PLUGIN_MANAGER_HPP

#include <string>
#include <memory>
#include <unordered_map>
#include <vector>
#include <functional>
#include <mutex>
#include <dlfcn.h>

namespace copilot {
namespace core {

// Forward declarations
class EventLoop;

/**
 * @brief Plugin API version for compatibility checking
 */
struct PluginAPIVersion {
    uint16_t major;
    uint16_t minor;
    uint16_t patch;

    bool is_compatible_with(const PluginAPIVersion& other) const {
        return major == other.major && minor >= other.minor;
    }
};

constexpr PluginAPIVersion CURRENT_PLUGIN_API_VERSION{1, 0, 0};

/**
 * @brief Plugin metadata
 */
struct PluginMetadata {
    std::string name;
    std::string version;
    std::string author;
    std::string description;
    std::vector<std::string> dependencies;
    PluginAPIVersion api_version;
    uint32_t capabilities_flags;
};

/**
 * @brief Plugin capability flags
 */
enum PluginCapabilities : uint32_t {
    CAPABILITY_NONE = 0,
    CAPABILITY_WINDOW_ACCESS = 1 << 0,      // Can access window management
    CAPABILITY_INPUT_CONTROL = 1 << 1,       // Can control keyboard/mouse
    CAPABILITY_SCREENSHOT = 1 << 2,          // Can capture screenshots
    CAPABILITY_PROCESS_MONITOR = 1 << 3,     // Can monitor processes
    CAPABILITY_FILESYSTEM_READ = 1 << 4,     // Can read files
    CAPABILITY_FILESYSTEM_WRITE = 1 << 5,    // Can write files
    CAPABILITY_NETWORK_ACCESS = 1 << 6,      // Can access network
    CAPABILITY_SYSTEM_CONTROL = 1 << 7,      // Can execute system commands
    CAPABILITY_AI_ACCESS = 1 << 8,           // Can access AI models
    CAPABILITY_ALL = 0xFFFFFFFF
};

/**
 * @brief Plugin state
 */
enum class PluginState {
    UNLOADED,
    LOADING,
    LOADED,
    INITIALIZING,
    ACTIVE,
    STOPPING,
    STOPPED,
    ERROR
};

/**
 * @brief Core API provided to plugins
 */
class PluginAPI {
public:
    virtual ~PluginAPI() = default;

    // Event system access
    virtual uint64_t subscribe_event(const std::string& event_type,
                                     std::function<void(const void*)> handler) = 0;
    virtual void unsubscribe_event(uint64_t subscription_id) = 0;
    virtual void emit_event(const std::string& event_type, const void* data) = 0;

    // Logging
    virtual void log_info(const std::string& message) = 0;
    virtual void log_warning(const std::string& message) = 0;
    virtual void log_error(const std::string& message) = 0;

    // Module access (based on capabilities)
    virtual void* get_module(const std::string& module_name) = 0;

    // Configuration
    virtual std::string get_config(const std::string& key, const std::string& default_value = "") = 0;
    virtual void set_config(const std::string& key, const std::string& value) = 0;

    // Timer support
    virtual uint64_t schedule_timer(uint32_t delay_ms, std::function<void()> callback) = 0;
    virtual void cancel_timer(uint64_t timer_id) = 0;
};

/**
 * @brief Base class for plugins (C++ plugins derive from this)
 */
class PluginBase {
public:
    virtual ~PluginBase() = default;

    /**
     * @brief Get plugin metadata
     */
    virtual PluginMetadata get_metadata() const = 0;

    /**
     * @brief Initialize the plugin
     * @param api Core API interface
     * @return true if initialization succeeded
     */
    virtual bool initialize(PluginAPI* api) = 0;

    /**
     * @brief Shutdown the plugin
     */
    virtual void shutdown() = 0;

    /**
     * @brief Called when plugin is enabled
     */
    virtual void on_enable() {}

    /**
     * @brief Called when plugin is disabled
     */
    virtual void on_disable() {}
};

/**
 * @brief Plugin info tracked by manager
 */
struct PluginInfo {
    std::string id;                          // Unique plugin ID
    std::string path;                        // Path to .so file
    void* handle;                            // dlopen handle
    std::unique_ptr<PluginBase> instance;    // Plugin instance
    PluginMetadata metadata;                 // Plugin metadata
    PluginState state;                       // Current state
    uint32_t granted_capabilities;           // Capabilities granted by user
    std::chrono::system_clock::time_point load_time;
    std::vector<uint64_t> active_subscriptions; // Event subscriptions
};

/**
 * @brief Plugin manager for dynamic loading/unloading
 */
class PluginManager {
public:
    explicit PluginManager(EventLoop* event_loop);
    ~PluginManager();

    // Disable copy/move
    PluginManager(const PluginManager&) = delete;
    PluginManager& operator=(const PluginManager&) = delete;

    /**
     * @brief Load a plugin from a shared library
     * @param plugin_path Path to .so file
     * @param granted_capabilities Capabilities to grant (or'd flags)
     * @return Plugin ID on success, empty string on failure
     */
    std::string load_plugin(const std::string& plugin_path,
                           uint32_t granted_capabilities = CAPABILITY_NONE);

    /**
     * @brief Unload a plugin
     * @param plugin_id Plugin ID returned by load_plugin
     * @return true if unloaded successfully
     */
    bool unload_plugin(const std::string& plugin_id);

    /**
     * @brief Reload a plugin (unload then load)
     * @param plugin_id Plugin ID
     * @return true if reloaded successfully
     */
    bool reload_plugin(const std::string& plugin_id);

    /**
     * @brief Enable a loaded plugin
     * @param plugin_id Plugin ID
     * @return true if enabled successfully
     */
    bool enable_plugin(const std::string& plugin_id);

    /**
     * @brief Disable an enabled plugin
     * @param plugin_id Plugin ID
     * @return true if disabled successfully
     */
    bool disable_plugin(const std::string& plugin_id);

    /**
     * @brief Get plugin information
     * @param plugin_id Plugin ID
     * @return Plugin info, or nullptr if not found
     */
    const PluginInfo* get_plugin_info(const std::string& plugin_id) const;

    /**
     * @brief Get all loaded plugins
     */
    std::vector<std::string> get_loaded_plugins() const;

    /**
     * @brief Check if plugin has specific capability
     * @param plugin_id Plugin ID
     * @param capability Capability to check
     * @return true if plugin has the capability
     */
    bool has_capability(const std::string& plugin_id, PluginCapabilities capability) const;

    /**
     * @brief Scan a directory for plugins
     * @param directory Directory to scan
     * @return List of found plugin paths
     */
    std::vector<std::string> scan_plugins(const std::string& directory);

    /**
     * @brief Set plugin search paths
     * @param paths Directories to search for plugins
     */
    void set_plugin_paths(const std::vector<std::string>& paths);

    /**
     * @brief Get plugin API interface for a plugin
     * @param plugin_id Plugin ID
     * @return PluginAPI interface, or nullptr
     */
    PluginAPI* get_plugin_api(const std::string& plugin_id);

private:
    // Load plugin from handle
    std::unique_ptr<PluginBase> load_plugin_instance(void* handle);

    // Verify plugin metadata and compatibility
    bool verify_plugin(const PluginMetadata& metadata);

    // Generate unique plugin ID
    std::string generate_plugin_id(const std::string& name);

    // Event loop reference
    EventLoop* event_loop_;

    // Loaded plugins
    std::unordered_map<std::string, std::unique_ptr<PluginInfo>> plugins_;
    mutable std::mutex plugins_mutex_;

    // Plugin search paths
    std::vector<std::string> plugin_paths_;

    // Next plugin ID counter
    std::atomic<uint64_t> next_id_{1};
};

} // namespace core
} // namespace copilot

// Plugin export macros (for plugin developers)
#define COPILOT_PLUGIN_EXPORT extern "C" __attribute__((visibility("default")))

// Plugin entry point
#define COPILOT_PLUGIN_ENTRY(PluginClass) \
    COPILOT_PLUGIN_EXPORT copilot::core::PluginBase* create_plugin() { \
        return new PluginClass(); \
    } \
    COPILOT_PLUGIN_EXPORT void destroy_plugin(copilot::core::PluginBase* plugin) { \
        delete plugin; \
    }

#endif // COPILOT_PLUGIN_MANAGER_HPP
