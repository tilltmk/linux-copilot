/**
 * @file thread_pool.cpp
 * @brief Implementation of high-performance thread pool
 */

#include "thread_pool.hpp"
#include <sched.h>
#include <pthread.h>

namespace copilot {
namespace core {

ThreadPool::ThreadPool(size_t num_threads)
    : stop_(false)
{
    if (num_threads == 0) {
        num_threads = std::thread::hardware_concurrency();
    }

    // Create per-thread queues
    thread_queues_.reserve(num_threads);
    for (size_t i = 0; i < num_threads; ++i) {
        thread_queues_.push_back(std::make_unique<ThreadQueue>());
    }

    // Start worker threads
    workers_.reserve(num_threads);
    for (size_t i = 0; i < num_threads; ++i) {
        workers_.push_back(
            std::make_unique<std::thread>(&ThreadPool::worker_thread, this, i)
        );
    }

    stats_ = {};
}

ThreadPool::~ThreadPool() {
    stop_ = true;
    global_cv_.notify_all();

    for (auto& worker : workers_) {
        if (worker && worker->joinable()) {
            worker->join();
        }
    }
}

uint64_t ThreadPool::submit_task(std::function<void()> func, TaskPriority priority) {
    Task task(std::move(func), priority);
    task.task_id = next_task_id_++;

    {
        std::lock_guard<std::mutex> lock(global_mutex_);
        global_queue_.push(std::move(task));
        stats_.total_tasks_submitted++;
    }

    global_cv_.notify_one();
    return task.task_id;
}

bool ThreadPool::cancel_task(uint64_t task_id) {
    std::lock_guard<std::mutex> lock(cancelled_mutex_);
    cancelled_tasks_.insert(task_id);
    return true;
}

bool ThreadPool::wait_all(uint32_t timeout_ms) {
    auto start = std::chrono::steady_clock::now();

    while (true) {
        size_t pending = 0;
        {
            std::lock_guard<std::mutex> lock(global_mutex_);
            // Can't get size of priority_queue directly
            // Would need custom implementation
        }

        if (pending == 0 && running_tasks_.load() == 0) {
            return true;
        }

        if (timeout_ms > 0) {
            auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
                std::chrono::steady_clock::now() - start).count();
            if (elapsed >= timeout_ms) {
                return false;
            }
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
}

void ThreadPool::clear_pending_tasks() {
    std::lock_guard<std::mutex> lock(global_mutex_);
    while (!global_queue_.empty()) {
        global_queue_.pop();
    }

    for (auto& queue : thread_queues_) {
        std::lock_guard<std::mutex> qlock(queue->mutex);
        while (!queue->queue.empty()) {
            queue->queue.pop();
        }
    }
}

size_t ThreadPool::pending_tasks() const {
    size_t count = 0;

    {
        std::lock_guard<std::mutex> lock(global_mutex_);
        // Would need custom priority_queue to get size
    }

    for (const auto& queue : thread_queues_) {
        std::lock_guard<std::mutex> lock(queue->mutex);
        // Same here
    }

    return count;
}

void ThreadPool::set_thread_affinity(size_t thread_index, int cpu_id) {
    if (thread_index >= workers_.size()) {
        return;
    }

    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(cpu_id, &cpuset);

    pthread_t thread = workers_[thread_index]->native_handle();
    pthread_setaffinity_np(thread, sizeof(cpu_set_t), &cpuset);
}

ThreadPool::Statistics ThreadPool::get_statistics() const {
    std::lock_guard<std::mutex> lock(stats_mutex_);
    return stats_;
}

void ThreadPool::reset_statistics() {
    std::lock_guard<std::mutex> lock(stats_mutex_);
    stats_ = {};
}

void ThreadPool::worker_thread(size_t thread_index) {
    while (!stop_) {
        Task task;
        bool got_task = false;

        // Try to get task from local queue first
        {
            std::lock_guard<std::mutex> lock(thread_queues_[thread_index]->mutex);
            if (!thread_queues_[thread_index]->queue.empty()) {
                task = thread_queues_[thread_index]->queue.top();
                thread_queues_[thread_index]->queue.pop();
                got_task = true;
            }
        }

        // Try global queue if local queue is empty
        if (!got_task) {
            std::unique_lock<std::mutex> lock(global_mutex_);
            global_cv_.wait_for(lock, std::chrono::milliseconds(100), [this] {
                return !global_queue_.empty() || stop_;
            });

            if (stop_) {
                break;
            }

            if (!global_queue_.empty()) {
                task = global_queue_.top();
                global_queue_.pop();
                got_task = true;
            }
        }

        // Try work stealing if still no task
        if (!got_task) {
            got_task = try_steal_task(thread_index, task);
        }

        if (!got_task) {
            continue;
        }

        // Check if task was cancelled
        {
            std::lock_guard<std::mutex> lock(cancelled_mutex_);
            if (cancelled_tasks_.count(task.task_id)) {
                cancelled_tasks_.erase(task.task_id);
                std::lock_guard<std::mutex> slock(stats_mutex_);
                stats_.tasks_cancelled++;
                continue;
            }
        }

        // Execute task
        running_tasks_++;

        auto wait_time = std::chrono::duration_cast<std::chrono::microseconds>(
            std::chrono::steady_clock::now() - task.submit_time).count();

        auto exec_start = std::chrono::steady_clock::now();

        try {
            task.func();
        } catch (...) {
            // Log exception
        }

        auto exec_time = std::chrono::duration_cast<std::chrono::microseconds>(
            std::chrono::steady_clock::now() - exec_start).count();

        running_tasks_--;

        // Update statistics
        {
            std::lock_guard<std::mutex> lock(stats_mutex_);
            stats_.tasks_completed++;
            stats_.average_wait_time_us = (stats_.average_wait_time_us * (stats_.tasks_completed - 1) +
                                           wait_time) / stats_.tasks_completed;
            stats_.average_execution_time_us = (stats_.average_execution_time_us * (stats_.tasks_completed - 1) +
                                                exec_time) / stats_.tasks_completed;

            if (thread_index < stats_.per_thread_task_count.size()) {
                stats_.per_thread_task_count[thread_index]++;
            } else {
                stats_.per_thread_task_count.resize(thread_index + 1);
                stats_.per_thread_task_count[thread_index] = 1;
            }
        }
    }
}

bool ThreadPool::try_steal_task(size_t thread_index, Task& task) {
    // Try to steal from other threads
    for (size_t i = 0; i < thread_queues_.size(); ++i) {
        if (i == thread_index) {
            continue;
        }

        std::lock_guard<std::mutex> lock(thread_queues_[i]->mutex);
        if (!thread_queues_[i]->queue.empty()) {
            task = thread_queues_[i]->queue.top();
            thread_queues_[i]->queue.pop();
            return true;
        }
    }

    return false;
}

bool ThreadPool::get_next_task(size_t thread_index, Task& task) {
    // Try local queue
    {
        std::lock_guard<std::mutex> lock(thread_queues_[thread_index]->mutex);
        if (!thread_queues_[thread_index]->queue.empty()) {
            task = thread_queues_[thread_index]->queue.top();
            thread_queues_[thread_index]->queue.pop();
            return true;
        }
    }

    // Try global queue
    {
        std::lock_guard<std::mutex> lock(global_mutex_);
        if (!global_queue_.empty()) {
            task = global_queue_.top();
            global_queue_.pop();
            return true;
        }
    }

    // Try work stealing
    return try_steal_task(thread_index, task);
}

} // namespace core
} // namespace copilot
