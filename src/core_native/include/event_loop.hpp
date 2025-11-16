/**
 * @file event_loop.hpp
 * @brief High-performance event loop implementation using epoll
 *
 * Provides asynchronous, non-blocking event processing with minimal latency.
 * Optimized for handling system events, window changes, and user input.
 */

#ifndef COPILOT_EVENT_LOOP_HPP
#define COPILOT_EVENT_LOOP_HPP

#include <functional>
#include <memory>
#include <unordered_map>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <thread>
#include <atomic>
#include <vector>
#include <chrono>
#include <sys/epoll.h>

namespace copilot {
namespace core {

/**
 * @brief Event types supported by the event loop
 */
enum class EventType {
    WINDOW_CREATED,
    WINDOW_DESTROYED,
    WINDOW_FOCUSED,
    WINDOW_MOVED,
    WINDOW_RESIZED,
    DESKTOP_CHANGED,
    PROCESS_STARTED,
    PROCESS_TERMINATED,
    INPUT_KEYBOARD,
    INPUT_MOUSE,
    HOTKEY_TRIGGERED,
    CUSTOM,
    TIMER,
    IPC_MESSAGE
};

/**
 * @brief Priority levels for event processing
 */
enum class EventPriority {
    CRITICAL = 0,  // Immediate processing (input events)
    HIGH = 1,      // High priority (window events)
    NORMAL = 2,    // Normal priority (most events)
    LOW = 3,       // Background tasks
    IDLE = 4       // Process when idle
};

/**
 * @brief Event data structure
 */
struct Event {
    EventType type;
    EventPriority priority;
    std::chrono::steady_clock::time_point timestamp;
    std::shared_ptr<void> data;
    std::string source;
    uint64_t sequence_id;

    Event(EventType t, EventPriority p = EventPriority::NORMAL)
        : type(t), priority(p), timestamp(std::chrono::steady_clock::now()),
          sequence_id(0) {}
};

/**
 * @brief Event handler callback type
 */
using EventHandler = std::function<void(const Event&)>;

/**
 * @brief Timer callback type
 */
using TimerCallback = std::function<void()>;

/**
 * @brief Priority queue comparator for events
 */
struct EventComparator {
    bool operator()(const std::shared_ptr<Event>& a, const std::shared_ptr<Event>& b) const {
        if (a->priority != b->priority) {
            return static_cast<int>(a->priority) > static_cast<int>(b->priority);
        }
        return a->sequence_id > b->sequence_id;
    }
};

/**
 * @brief High-performance event loop with epoll backend
 *
 * Features:
 * - Lock-free event queue where possible
 * - Priority-based event processing
 * - Timer support with nanosecond precision
 * - File descriptor monitoring
 * - Thread-safe event emission
 * - Automatic load balancing
 */
class EventLoop {
public:
    EventLoop();
    ~EventLoop();

    // Disable copy/move
    EventLoop(const EventLoop&) = delete;
    EventLoop& operator=(const EventLoop&) = delete;

    /**
     * @brief Start the event loop
     * @param num_worker_threads Number of worker threads for event processing
     * @return true if started successfully
     */
    bool start(size_t num_worker_threads = std::thread::hardware_concurrency());

    /**
     * @brief Stop the event loop gracefully
     * @param timeout_ms Maximum time to wait for graceful shutdown
     */
    void stop(uint32_t timeout_ms = 5000);

    /**
     * @brief Check if event loop is running
     */
    bool is_running() const { return running_.load(); }

    /**
     * @brief Subscribe to an event type
     * @param type Event type to subscribe to
     * @param handler Callback function
     * @return Subscription ID (use to unsubscribe)
     */
    uint64_t subscribe(EventType type, EventHandler handler);

    /**
     * @brief Unsubscribe from an event
     * @param subscription_id ID returned by subscribe()
     */
    void unsubscribe(uint64_t subscription_id);

    /**
     * @brief Emit an event
     * @param event Event to emit
     */
    void emit(std::shared_ptr<Event> event);

    /**
     * @brief Schedule a one-time timer
     * @param delay_ms Delay in milliseconds
     * @param callback Function to call
     * @return Timer ID (use to cancel)
     */
    uint64_t schedule_timer(uint32_t delay_ms, TimerCallback callback);

    /**
     * @brief Schedule a recurring timer
     * @param interval_ms Interval in milliseconds
     * @param callback Function to call
     * @return Timer ID (use to cancel)
     */
    uint64_t schedule_recurring_timer(uint32_t interval_ms, TimerCallback callback);

    /**
     * @brief Cancel a timer
     * @param timer_id ID returned by schedule_timer() or schedule_recurring_timer()
     */
    void cancel_timer(uint64_t timer_id);

    /**
     * @brief Add a file descriptor to monitor
     * @param fd File descriptor
     * @param events Epoll events to monitor (EPOLLIN, EPOLLOUT, etc.)
     * @param handler Callback when events occur
     * @return true if added successfully
     */
    bool add_fd(int fd, uint32_t events, std::function<void(uint32_t)> handler);

    /**
     * @brief Remove a file descriptor from monitoring
     * @param fd File descriptor
     */
    void remove_fd(int fd);

    /**
     * @brief Get event processing statistics
     */
    struct Statistics {
        uint64_t events_processed;
        uint64_t events_pending;
        uint64_t average_latency_ns;
        uint64_t max_latency_ns;
        double cpu_usage;
    };

    Statistics get_statistics() const;

    /**
     * @brief Reset statistics
     */
    void reset_statistics();

private:
    // Event loop thread function
    void event_loop_thread();

    // Worker thread function
    void worker_thread();

    // Timer management thread
    void timer_thread();

    // Process pending events
    void process_events();

    // Epoll file descriptor
    int epoll_fd_;

    // Event eventfd for waking up epoll
    int event_fd_;

    // Running flag
    std::atomic<bool> running_;

    // Shutdown flag
    std::atomic<bool> shutdown_;

    // Event loop thread
    std::unique_ptr<std::thread> loop_thread_;

    // Worker threads
    std::vector<std::unique_ptr<std::thread>> worker_threads_;

    // Timer thread
    std::unique_ptr<std::thread> timer_thread_;

    // Event queue (priority queue)
    std::priority_queue<std::shared_ptr<Event>,
                       std::vector<std::shared_ptr<Event>>,
                       EventComparator> event_queue_;

    // Mutex for event queue
    mutable std::mutex queue_mutex_;

    // Condition variable for event queue
    std::condition_variable queue_cv_;

    // Event handlers
    std::unordered_map<EventType, std::unordered_map<uint64_t, EventHandler>> handlers_;
    mutable std::mutex handlers_mutex_;

    // File descriptor handlers
    std::unordered_map<int, std::function<void(uint32_t)>> fd_handlers_;
    mutable std::mutex fd_mutex_;

    // Timer structures
    struct Timer {
        uint64_t id;
        std::chrono::steady_clock::time_point next_trigger;
        std::chrono::milliseconds interval;
        TimerCallback callback;
        bool recurring;
        bool cancelled;
    };

    std::vector<Timer> timers_;
    mutable std::mutex timers_mutex_;
    std::condition_variable timers_cv_;

    // Counters
    std::atomic<uint64_t> next_subscription_id_{1};
    std::atomic<uint64_t> next_sequence_id_{1};
    std::atomic<uint64_t> next_timer_id_{1};

    // Statistics
    mutable std::mutex stats_mutex_;
    Statistics stats_;
    std::chrono::steady_clock::time_point stats_start_time_;
};

} // namespace core
} // namespace copilot

#endif // COPILOT_EVENT_LOOP_HPP
