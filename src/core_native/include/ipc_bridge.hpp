/**
 * @file ipc_bridge.hpp
 * @brief Inter-Process Communication bridge between C++ core and Python/UI
 *
 * Provides high-performance IPC using shared memory and message passing.
 * Enables seamless communication between the C++ core and Python/UI layers.
 */

#ifndef COPILOT_IPC_BRIDGE_HPP
#define COPILOT_IPC_BRIDGE_HPP

#include <string>
#include <memory>
#include <functional>
#include <vector>
#include <mutex>
#include <atomic>
#include <sys/types.h>

namespace copilot {
namespace core {

/**
 * @brief IPC message types
 */
enum class IPCMessageType {
    // Requests
    REQUEST_WINDOW_LIST,
    REQUEST_WINDOW_FOCUS,
    REQUEST_WINDOW_MOVE,
    REQUEST_WINDOW_RESIZE,
    REQUEST_INPUT_KEYBOARD,
    REQUEST_INPUT_MOUSE,
    REQUEST_SCREENSHOT,
    REQUEST_PLUGIN_LOAD,
    REQUEST_PLUGIN_UNLOAD,
    REQUEST_AI_INFERENCE,

    // Responses
    RESPONSE_SUCCESS,
    RESPONSE_ERROR,
    RESPONSE_DATA,

    // Events
    EVENT_WINDOW_CHANGED,
    EVENT_DESKTOP_CHANGED,
    EVENT_PROCESS_STARTED,
    EVENT_HOTKEY_TRIGGERED,
    EVENT_AI_RESPONSE,

    // System
    PING,
    PONG,
    SHUTDOWN
};

/**
 * @brief IPC message structure
 */
struct IPCMessage {
    IPCMessageType type;
    uint64_t request_id;
    uint32_t data_length;
    std::vector<uint8_t> data;
    std::chrono::steady_clock::time_point timestamp;

    IPCMessage() : type(IPCMessageType::PING), request_id(0), data_length(0) {}
};

/**
 * @brief IPC transport type
 */
enum class IPCTransport {
    UNIX_SOCKET,      // Unix domain sockets (default)
    SHARED_MEMORY,    // Shared memory with message queue
    DBUS,             // D-Bus (for system integration)
    TCP_SOCKET        // TCP (for remote access)
};

/**
 * @brief IPC message handler callback
 */
using IPCMessageHandler = std::function<void(const IPCMessage&)>;

/**
 * @brief High-performance IPC bridge
 *
 * Features:
 * - Multiple transport backends
 * - Zero-copy shared memory mode
 * - Async message handling
 * - Request/response pattern support
 * - Binary serialization for efficiency
 * - Auto-reconnect on connection loss
 */
class IPCBridge {
public:
    IPCBridge();
    ~IPCBridge();

    // Disable copy/move
    IPCBridge(const IPCBridge&) = delete;
    IPCBridge& operator=(const IPCBridge&) = delete;

    /**
     * @brief Initialize IPC bridge as server
     * @param endpoint IPC endpoint (socket path, shared memory name, etc.)
     * @param transport Transport type to use
     * @return true if initialized successfully
     */
    bool initialize_server(const std::string& endpoint,
                          IPCTransport transport = IPCTransport::UNIX_SOCKET);

    /**
     * @brief Initialize IPC bridge as client
     * @param endpoint IPC endpoint to connect to
     * @param transport Transport type to use
     * @return true if connected successfully
     */
    bool initialize_client(const std::string& endpoint,
                          IPCTransport transport = IPCTransport::UNIX_SOCKET);

    /**
     * @brief Shutdown IPC bridge
     */
    void shutdown();

    /**
     * @brief Check if connected
     */
    bool is_connected() const { return connected_.load(); }

    /**
     * @brief Send a message
     * @param message Message to send
     * @return true if sent successfully
     */
    bool send_message(const IPCMessage& message);

    /**
     * @brief Send a request and wait for response
     * @param request Request message
     * @param timeout_ms Timeout in milliseconds
     * @return Response message (empty if timeout)
     */
    IPCMessage send_request(const IPCMessage& request, uint32_t timeout_ms = 5000);

    /**
     * @brief Send a response to a request
     * @param request_id ID of the original request
     * @param response Response data
     * @return true if sent successfully
     */
    bool send_response(uint64_t request_id, const IPCMessage& response);

    /**
     * @brief Register message handler
     * @param type Message type to handle
     * @param handler Callback function
     */
    void register_handler(IPCMessageType type, IPCMessageHandler handler);

    /**
     * @brief Unregister message handler
     * @param type Message type
     */
    void unregister_handler(IPCMessageType type);

    /**
     * @brief Get IPC statistics
     */
    struct Statistics {
        uint64_t messages_sent;
        uint64_t messages_received;
        uint64_t bytes_sent;
        uint64_t bytes_received;
        uint64_t errors;
        double average_latency_us;
    };

    Statistics get_statistics() const;

    /**
     * @brief Enable/disable auto-reconnect
     * @param enable true to enable auto-reconnect
     * @param retry_interval_ms Interval between reconnect attempts
     */
    void set_auto_reconnect(bool enable, uint32_t retry_interval_ms = 1000);

private:
    // Server accept loop
    void server_accept_loop();

    // Message receive loop
    void receive_loop();

    // Handle incoming message
    void handle_message(const IPCMessage& message);

    // Send raw data
    bool send_raw(const void* data, size_t length);

    // Receive raw data
    bool receive_raw(void* data, size_t length);

    // Serialize message
    std::vector<uint8_t> serialize_message(const IPCMessage& message);

    // Deserialize message
    IPCMessage deserialize_message(const std::vector<uint8_t>& data);

    // Transport-specific implementations
    struct UnixSocketTransport;
    struct SharedMemoryTransport;
    struct DBusTransport;
    struct TCPTransport;

    // Current transport
    IPCTransport transport_type_;
    std::unique_ptr<void, void(*)(void*)> transport_;

    // Socket file descriptor
    int socket_fd_;
    int client_fd_;

    // Connection state
    std::atomic<bool> connected_;
    std::atomic<bool> is_server_;
    std::atomic<bool> running_;

    // Threads
    std::unique_ptr<std::thread> accept_thread_;
    std::unique_ptr<std::thread> receive_thread_;

    // Message handlers
    std::unordered_map<IPCMessageType, IPCMessageHandler> handlers_;
    mutable std::mutex handlers_mutex_;

    // Pending requests (for request/response pattern)
    struct PendingRequest {
        uint64_t request_id;
        std::promise<IPCMessage> promise;
        std::chrono::steady_clock::time_point timeout;
    };
    std::unordered_map<uint64_t, std::shared_ptr<PendingRequest>> pending_requests_;
    mutable std::mutex requests_mutex_;

    // Statistics
    mutable std::mutex stats_mutex_;
    Statistics stats_;

    // Auto-reconnect
    bool auto_reconnect_;
    uint32_t reconnect_interval_ms_;
    std::string reconnect_endpoint_;

    // Request ID counter
    std::atomic<uint64_t> next_request_id_{1};
};

/**
 * @brief Python binding helper for IPC messages
 */
class IPCMessageBuilder {
public:
    static IPCMessage create_window_list_request();
    static IPCMessage create_window_focus_request(uint64_t window_id);
    static IPCMessage create_window_move_request(uint64_t window_id, int x, int y);
    static IPCMessage create_keyboard_input_request(const std::string& text);
    static IPCMessage create_screenshot_request(int x, int y, int width, int height);
    static IPCMessage create_ai_inference_request(const std::string& model,
                                                  const std::string& prompt);

    static IPCMessage create_success_response(uint64_t request_id);
    static IPCMessage create_error_response(uint64_t request_id, const std::string& error);
    static IPCMessage create_data_response(uint64_t request_id, const std::vector<uint8_t>& data);

    static IPCMessage create_event(IPCMessageType event_type, const std::vector<uint8_t>& data);
};

} // namespace core
} // namespace copilot

#endif // COPILOT_IPC_BRIDGE_HPP
