/**
 * @file thread_pool.hpp
 * @brief High-performance thread pool for parallel task execution
 *
 * Provides efficient task scheduling and execution with work stealing.
 * Optimized for low latency and high throughput.
 */

#ifndef COPILOT_THREAD_POOL_HPP
#define COPILOT_THREAD_POOL_HPP

#include <vector>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <future>
#include <atomic>
#include <memory>

namespace copilot {
namespace core {

/**
 * @brief Task priority levels
 */
enum class TaskPriority {
    CRITICAL = 0,
    HIGH = 1,
    NORMAL = 2,
    LOW = 3,
    BACKGROUND = 4
};

/**
 * @brief Task wrapper
 */
struct Task {
    std::function<void()> func;
    TaskPriority priority;
    std::chrono::steady_clock::time_point submit_time;
    uint64_t task_id;

    Task() : priority(TaskPriority::NORMAL), task_id(0) {}
    Task(std::function<void()> f, TaskPriority p)
        : func(std::move(f)), priority(p),
          submit_time(std::chrono::steady_clock::now()), task_id(0) {}
};

/**
 * @brief Task comparator for priority queue
 */
struct TaskComparator {
    bool operator()(const Task& a, const Task& b) const {
        if (a.priority != b.priority) {
            return static_cast<int>(a.priority) > static_cast<int>(b.priority);
        }
        return a.task_id > b.task_id;
    }
};

/**
 * @brief High-performance thread pool with work stealing
 *
 * Features:
 * - Priority-based task scheduling
 * - Work stealing for load balancing
 * - Task cancellation support
 * - Future-based result retrieval
 * - Thread affinity control
 * - Per-thread task queues
 */
class ThreadPool {
public:
    /**
     * @brief Constructor
     * @param num_threads Number of worker threads (0 = hardware concurrency)
     */
    explicit ThreadPool(size_t num_threads = 0);

    /**
     * @brief Destructor - waits for all tasks to complete
     */
    ~ThreadPool();

    // Disable copy/move
    ThreadPool(const ThreadPool&) = delete;
    ThreadPool& operator=(const ThreadPool&) = delete;

    /**
     * @brief Submit a task for execution
     * @param func Function to execute
     * @param priority Task priority
     * @return Future for the result
     */
    template<typename F, typename... Args>
    auto submit(F&& func, Args&&... args, TaskPriority priority = TaskPriority::NORMAL)
        -> std::future<typename std::invoke_result<F, Args...>::type>;

    /**
     * @brief Submit a task and get task ID
     * @param func Function to execute
     * @param priority Task priority
     * @return Task ID (can be used for cancellation)
     */
    uint64_t submit_task(std::function<void()> func, TaskPriority priority = TaskPriority::NORMAL);

    /**
     * @brief Cancel a pending task
     * @param task_id Task ID returned by submit_task()
     * @return true if cancelled (false if already running/completed)
     */
    bool cancel_task(uint64_t task_id);

    /**
     * @brief Wait for all pending tasks to complete
     * @param timeout_ms Maximum time to wait (0 = infinite)
     * @return true if all tasks completed, false if timeout
     */
    bool wait_all(uint32_t timeout_ms = 0);

    /**
     * @brief Clear all pending tasks
     */
    void clear_pending_tasks();

    /**
     * @brief Get number of pending tasks
     */
    size_t pending_tasks() const;

    /**
     * @brief Get number of running tasks
     */
    size_t running_tasks() const { return running_tasks_.load(); }

    /**
     * @brief Get number of worker threads
     */
    size_t thread_count() const { return workers_.size(); }

    /**
     * @brief Set thread affinity for a worker
     * @param thread_index Worker thread index
     * @param cpu_id CPU core ID
     */
    void set_thread_affinity(size_t thread_index, int cpu_id);

    /**
     * @brief Get statistics
     */
    struct Statistics {
        uint64_t tasks_completed;
        uint64_t tasks_cancelled;
        uint64_t total_tasks_submitted;
        double average_wait_time_us;
        double average_execution_time_us;
        std::vector<size_t> per_thread_task_count;
    };

    Statistics get_statistics() const;

    /**
     * @brief Reset statistics
     */
    void reset_statistics();

private:
    // Worker thread function
    void worker_thread(size_t thread_index);

    // Try to steal work from another thread
    bool try_steal_task(size_t thread_index, Task& task);

    // Get next task for a worker
    bool get_next_task(size_t thread_index, Task& task);

    // Worker threads
    std::vector<std::unique_ptr<std::thread>> workers_;

    // Global task queue (shared)
    std::priority_queue<Task, std::vector<Task>, TaskComparator> global_queue_;
    mutable std::mutex global_mutex_;
    std::condition_variable global_cv_;

    // Per-thread task queues for work stealing
    struct ThreadQueue {
        std::priority_queue<Task, std::vector<Task>, TaskComparator> queue;
        mutable std::mutex mutex;
    };
    std::vector<std::unique_ptr<ThreadQueue>> thread_queues_;

    // Cancelled tasks
    std::unordered_set<uint64_t> cancelled_tasks_;
    mutable std::mutex cancelled_mutex_;

    // Running state
    std::atomic<bool> stop_;
    std::atomic<size_t> running_tasks_{0};

    // Task ID counter
    std::atomic<uint64_t> next_task_id_{1};

    // Statistics
    mutable std::mutex stats_mutex_;
    Statistics stats_;
};

// Template implementation
template<typename F, typename... Args>
auto ThreadPool::submit(F&& func, Args&&... args, TaskPriority priority)
    -> std::future<typename std::invoke_result<F, Args...>::type>
{
    using return_type = typename std::invoke_result<F, Args...>::type;

    auto task = std::make_shared<std::packaged_task<return_type()>>(
        std::bind(std::forward<F>(func), std::forward<Args>(args)...)
    );

    std::future<return_type> result = task->get_future();

    {
        std::unique_lock<std::mutex> lock(global_mutex_);

        if (stop_) {
            throw std::runtime_error("ThreadPool is stopped");
        }

        Task t([task]() { (*task)(); }, priority);
        t.task_id = next_task_id_++;

        global_queue_.push(std::move(t));
        stats_.total_tasks_submitted++;
    }

    global_cv_.notify_one();
    return result;
}

} // namespace core
} // namespace copilot

#endif // COPILOT_THREAD_POOL_HPP
