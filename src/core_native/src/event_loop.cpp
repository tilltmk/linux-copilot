/**
 * @file event_loop.cpp
 * @brief Implementation of high-performance event loop
 */

#include "event_loop.hpp"
#include <sys/epoll.h>
#include <sys/eventfd.h>
#include <unistd.h>
#include <algorithm>
#include <iostream>
#include <cstring>

namespace copilot {
namespace core {

EventLoop::EventLoop()
    : epoll_fd_(-1), event_fd_(-1), running_(false), shutdown_(false)
{
    // Create epoll instance
    epoll_fd_ = epoll_create1(EPOLL_CLOEXEC);
    if (epoll_fd_ < 0) {
        throw std::runtime_error("Failed to create epoll instance: " + std::string(strerror(errno)));
    }

    // Create eventfd for waking up epoll
    event_fd_ = eventfd(0, EFD_NONBLOCK | EFD_CLOEXEC);
    if (event_fd_ < 0) {
        close(epoll_fd_);
        throw std::runtime_error("Failed to create eventfd: " + std::string(strerror(errno)));
    }

    // Add eventfd to epoll
    struct epoll_event ev;
    ev.events = EPOLLIN;
    ev.data.fd = event_fd_;
    if (epoll_ctl(epoll_fd_, EPOLL_CTL_ADD, event_fd_, &ev) < 0) {
        close(event_fd_);
        close(epoll_fd_);
        throw std::runtime_error("Failed to add eventfd to epoll");
    }

    // Initialize statistics
    stats_ = {};
    stats_start_time_ = std::chrono::steady_clock::now();
}

EventLoop::~EventLoop() {
    if (running_.load()) {
        stop();
    }

    if (event_fd_ >= 0) {
        close(event_fd_);
    }
    if (epoll_fd_ >= 0) {
        close(epoll_fd_);
    }
}

bool EventLoop::start(size_t num_worker_threads) {
    if (running_.load()) {
        return false;
    }

    running_ = true;
    shutdown_ = false;

    // Start event loop thread
    loop_thread_ = std::make_unique<std::thread>(&EventLoop::event_loop_thread, this);

    // Start worker threads
    for (size_t i = 0; i < num_worker_threads; ++i) {
        worker_threads_.push_back(
            std::make_unique<std::thread>(&EventLoop::worker_thread, this)
        );
    }

    // Start timer thread
    timer_thread_ = std::make_unique<std::thread>(&EventLoop::timer_thread, this);

    return true;
}

void EventLoop::stop(uint32_t timeout_ms) {
    if (!running_.load()) {
        return;
    }

    shutdown_ = true;

    // Wake up all threads
    queue_cv_.notify_all();
    timers_cv_.notify_all();

    // Wake up epoll
    uint64_t val = 1;
    write(event_fd_, &val, sizeof(val));

    // Wait for threads with timeout
    auto wait_start = std::chrono::steady_clock::now();

    if (loop_thread_ && loop_thread_->joinable()) {
        if (timeout_ms > 0) {
            auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
                std::chrono::steady_clock::now() - wait_start).count();
            if (elapsed < timeout_ms) {
                loop_thread_->join();
            }
        } else {
            loop_thread_->join();
        }
    }

    for (auto& worker : worker_threads_) {
        if (worker && worker->joinable()) {
            worker->join();
        }
    }

    if (timer_thread_ && timer_thread_->joinable()) {
        timer_thread_->join();
    }

    running_ = false;
}

uint64_t EventLoop::subscribe(EventType type, EventHandler handler) {
    std::lock_guard<std::mutex> lock(handlers_mutex_);
    uint64_t id = next_subscription_id_++;
    handlers_[type][id] = std::move(handler);
    return id;
}

void EventLoop::unsubscribe(uint64_t subscription_id) {
    std::lock_guard<std::mutex> lock(handlers_mutex_);
    for (auto& [type, handlers] : handlers_) {
        handlers.erase(subscription_id);
    }
}

void EventLoop::emit(std::shared_ptr<Event> event) {
    if (!running_.load()) {
        return;
    }

    event->sequence_id = next_sequence_id_++;
    event->timestamp = std::chrono::steady_clock::now();

    {
        std::lock_guard<std::mutex> lock(queue_mutex_);
        event_queue_.push(event);
    }

    queue_cv_.notify_one();

    // Wake up epoll
    uint64_t val = 1;
    write(event_fd_, &val, sizeof(val));
}

uint64_t EventLoop::schedule_timer(uint32_t delay_ms, TimerCallback callback) {
    std::lock_guard<std::mutex> lock(timers_mutex_);

    Timer timer;
    timer.id = next_timer_id_++;
    timer.next_trigger = std::chrono::steady_clock::now() +
                         std::chrono::milliseconds(delay_ms);
    timer.interval = std::chrono::milliseconds(delay_ms);
    timer.callback = std::move(callback);
    timer.recurring = false;
    timer.cancelled = false;

    timers_.push_back(std::move(timer));
    timers_cv_.notify_one();

    return timer.id;
}

uint64_t EventLoop::schedule_recurring_timer(uint32_t interval_ms, TimerCallback callback) {
    std::lock_guard<std::mutex> lock(timers_mutex_);

    Timer timer;
    timer.id = next_timer_id_++;
    timer.next_trigger = std::chrono::steady_clock::now() +
                         std::chrono::milliseconds(interval_ms);
    timer.interval = std::chrono::milliseconds(interval_ms);
    timer.callback = std::move(callback);
    timer.recurring = true;
    timer.cancelled = false;

    timers_.push_back(std::move(timer));
    timers_cv_.notify_one();

    return timer.id;
}

void EventLoop::cancel_timer(uint64_t timer_id) {
    std::lock_guard<std::mutex> lock(timers_mutex_);
    for (auto& timer : timers_) {
        if (timer.id == timer_id) {
            timer.cancelled = true;
            break;
        }
    }
}

bool EventLoop::add_fd(int fd, uint32_t events, std::function<void(uint32_t)> handler) {
    std::lock_guard<std::mutex> lock(fd_mutex_);

    struct epoll_event ev;
    ev.events = events;
    ev.data.fd = fd;

    if (epoll_ctl(epoll_fd_, EPOLL_CTL_ADD, fd, &ev) < 0) {
        return false;
    }

    fd_handlers_[fd] = std::move(handler);
    return true;
}

void EventLoop::remove_fd(int fd) {
    std::lock_guard<std::mutex> lock(fd_mutex_);
    epoll_ctl(epoll_fd_, EPOLL_CTL_DEL, fd, nullptr);
    fd_handlers_.erase(fd);
}

void EventLoop::event_loop_thread() {
    const int MAX_EVENTS = 64;
    struct epoll_event events[MAX_EVENTS];

    while (!shutdown_.load()) {
        int nfds = epoll_wait(epoll_fd_, events, MAX_EVENTS, 100);

        if (nfds < 0) {
            if (errno == EINTR) {
                continue;
            }
            break;
        }

        for (int i = 0; i < nfds; ++i) {
            int fd = events[i].data.fd;

            if (fd == event_fd_) {
                // Clear eventfd
                uint64_t val;
                read(event_fd_, &val, sizeof(val));
                continue;
            }

            // Call fd handler
            std::lock_guard<std::mutex> lock(fd_mutex_);
            auto it = fd_handlers_.find(fd);
            if (it != fd_handlers_.end()) {
                it->second(events[i].events);
            }
        }

        // Process events
        process_events();
    }
}

void EventLoop::worker_thread() {
    while (!shutdown_.load()) {
        std::shared_ptr<Event> event;

        {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            queue_cv_.wait(lock, [this] {
                return !event_queue_.empty() || shutdown_.load();
            });

            if (shutdown_.load() && event_queue_.empty()) {
                break;
            }

            if (!event_queue_.empty()) {
                event = event_queue_.top();
                event_queue_.pop();
            }
        }

        if (!event) {
            continue;
        }

        auto start_time = std::chrono::steady_clock::now();

        // Call handlers for this event type
        {
            std::lock_guard<std::mutex> lock(handlers_mutex_);
            auto it = handlers_.find(event->type);
            if (it != handlers_.end()) {
                for (const auto& [id, handler] : it->second) {
                    try {
                        handler(*event);
                    } catch (const std::exception& e) {
                        // Log error (TODO: integrate with logging system)
                    }
                }
            }
        }

        auto end_time = std::chrono::steady_clock::now();
        auto latency = std::chrono::duration_cast<std::chrono::nanoseconds>(
            end_time - event->timestamp).count();

        // Update statistics
        {
            std::lock_guard<std::mutex> lock(stats_mutex_);
            stats_.events_processed++;
            stats_.average_latency_ns = (stats_.average_latency_ns * (stats_.events_processed - 1) +
                                         latency) / stats_.events_processed;
            stats_.max_latency_ns = std::max(stats_.max_latency_ns, static_cast<uint64_t>(latency));
        }
    }
}

void EventLoop::timer_thread() {
    while (!shutdown_.load()) {
        std::unique_lock<std::mutex> lock(timers_mutex_);

        auto now = std::chrono::steady_clock::now();
        bool triggered_any = false;

        for (auto it = timers_.begin(); it != timers_.end();) {
            if (it->cancelled) {
                it = timers_.erase(it);
                continue;
            }

            if (now >= it->next_trigger) {
                // Trigger timer
                auto callback = it->callback;
                lock.unlock();

                try {
                    callback();
                } catch (const std::exception& e) {
                    // Log error
                }

                lock.lock();
                triggered_any = true;

                if (it->recurring) {
                    it->next_trigger = now + it->interval;
                    ++it;
                } else {
                    it = timers_.erase(it);
                }
            } else {
                ++it;
            }
        }

        if (!triggered_any && !timers_.empty()) {
            // Wait until next timer
            auto next = std::min_element(timers_.begin(), timers_.end(),
                [](const Timer& a, const Timer& b) {
                    return a.next_trigger < b.next_trigger;
                });

            if (next != timers_.end()) {
                timers_cv_.wait_until(lock, next->next_trigger);
            }
        } else {
            timers_cv_.wait_for(lock, std::chrono::milliseconds(100));
        }
    }
}

void EventLoop::process_events() {
    // This is called from the event loop thread
    // Can be used for additional event processing if needed
}

EventLoop::Statistics EventLoop::get_statistics() const {
    std::lock_guard<std::mutex> lock(stats_mutex_);
    auto stats = stats_;
    stats.events_pending = 0;

    {
        std::lock_guard<std::mutex> qlock(queue_mutex_);
        // Note: Can't get size of priority_queue directly
        // Would need custom implementation for this
    }

    return stats;
}

void EventLoop::reset_statistics() {
    std::lock_guard<std::mutex> lock(stats_mutex_);
    stats_ = {};
    stats_start_time_ = std::chrono::steady_clock::now();
}

} // namespace core
} // namespace copilot
