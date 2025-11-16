/**
 * @file test_event_loop.cpp
 * @brief Unit tests for event loop
 */

#include "event_loop.hpp"
#include <gtest/gtest.h>
#include <atomic>
#include <chrono>
#include <thread>

using namespace copilot::core;

class EventLoopTest : public ::testing::Test {
protected:
    void SetUp() override {
        event_loop = std::make_unique<EventLoop>();
    }

    void TearDown() override {
        if (event_loop && event_loop->is_running()) {
            event_loop->stop();
        }
        event_loop.reset();
    }

    std::unique_ptr<EventLoop> event_loop;
};

TEST_F(EventLoopTest, StartStop) {
    EXPECT_FALSE(event_loop->is_running());

    EXPECT_TRUE(event_loop->start(2));
    EXPECT_TRUE(event_loop->is_running());

    event_loop->stop();
    EXPECT_FALSE(event_loop->is_running());
}

TEST_F(EventLoopTest, EventEmitAndSubscribe) {
    std::atomic<int> counter{0};

    auto sub_id = event_loop->subscribe(EventType::WINDOW_FOCUSED,
        [&counter](const Event& event) {
            counter++;
        });

    EXPECT_TRUE(event_loop->start());

    // Emit events
    for (int i = 0; i < 10; ++i) {
        auto event = std::make_shared<Event>(EventType::WINDOW_FOCUSED);
        event_loop->emit(event);
    }

    // Wait for processing
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    EXPECT_EQ(counter.load(), 10);

    event_loop->unsubscribe(sub_id);
}

TEST_F(EventLoopTest, EventPriority) {
    std::vector<int> execution_order;
    std::mutex order_mutex;

    event_loop->subscribe(EventType::CUSTOM,
        [&execution_order, &order_mutex](const Event& event) {
            std::lock_guard<std::mutex> lock(order_mutex);
            execution_order.push_back(static_cast<int>(event.priority));
        });

    EXPECT_TRUE(event_loop->start());

    // Emit events with different priorities
    for (int i = 0; i < 5; ++i) {
        auto event = std::make_shared<Event>(EventType::CUSTOM, EventPriority::LOW);
        event_loop->emit(event);
    }

    for (int i = 0; i < 5; ++i) {
        auto event = std::make_shared<Event>(EventType::CUSTOM, EventPriority::CRITICAL);
        event_loop->emit(event);
    }

    // Wait for processing
    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    // Critical events should be processed first
    EXPECT_EQ(execution_order.size(), 10);
    for (int i = 0; i < 5; ++i) {
        EXPECT_EQ(execution_order[i], static_cast<int>(EventPriority::CRITICAL));
    }
}

TEST_F(EventLoopTest, TimerOneShot) {
    std::atomic<bool> timer_fired{false};

    EXPECT_TRUE(event_loop->start());

    auto timer_id = event_loop->schedule_timer(100, [&timer_fired]() {
        timer_fired = true;
    });

    EXPECT_GT(timer_id, 0);

    // Wait for timer
    std::this_thread::sleep_for(std::chrono::milliseconds(150));

    EXPECT_TRUE(timer_fired.load());
}

TEST_F(EventLoopTest, TimerRecurring) {
    std::atomic<int> timer_count{0};

    EXPECT_TRUE(event_loop->start());

    auto timer_id = event_loop->schedule_recurring_timer(50, [&timer_count]() {
        timer_count++;
    });

    // Wait for multiple firings
    std::this_thread::sleep_for(std::chrono::milliseconds(250));

    // Should fire approximately 5 times (250ms / 50ms)
    EXPECT_GE(timer_count.load(), 4);
    EXPECT_LE(timer_count.load(), 6);

    event_loop->cancel_timer(timer_id);

    // Wait a bit more
    int count_after_cancel = timer_count.load();
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    // Count shouldn't increase after cancellation
    EXPECT_EQ(timer_count.load(), count_after_cancel);
}

TEST_F(EventLoopTest, MultipleSubscribers) {
    std::atomic<int> counter1{0};
    std::atomic<int> counter2{0};

    auto sub1 = event_loop->subscribe(EventType::WINDOW_MOVED,
        [&counter1](const Event& event) {
            counter1++;
        });

    auto sub2 = event_loop->subscribe(EventType::WINDOW_MOVED,
        [&counter2](const Event& event) {
            counter2++;
        });

    EXPECT_TRUE(event_loop->start());

    // Emit event
    auto event = std::make_shared<Event>(EventType::WINDOW_MOVED);
    event_loop->emit(event);

    // Wait for processing
    std::this_thread::sleep_for(std::chrono::milliseconds(50));

    // Both subscribers should receive the event
    EXPECT_EQ(counter1.load(), 1);
    EXPECT_EQ(counter2.load(), 1);
}

TEST_F(EventLoopTest, Performance) {
    const int NUM_EVENTS = 10000;
    std::atomic<int> counter{0};

    auto sub_id = event_loop->subscribe(EventType::CUSTOM,
        [&counter](const Event& event) {
            counter++;
        });

    EXPECT_TRUE(event_loop->start(4)); // 4 worker threads

    auto start = std::chrono::steady_clock::now();

    // Emit many events
    for (int i = 0; i < NUM_EVENTS; ++i) {
        auto event = std::make_shared<Event>(EventType::CUSTOM);
        event_loop->emit(event);
    }

    // Wait for all events to be processed
    while (counter.load() < NUM_EVENTS) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }

    auto end = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    EXPECT_EQ(counter.load(), NUM_EVENTS);

    // Should process 10k events in less than 1 second
    EXPECT_LT(duration.count(), 1000);

    // Calculate throughput
    double throughput = static_cast<double>(NUM_EVENTS) / (duration.count() / 1000.0);
    std::cout << "Event throughput: " << throughput << " events/second" << std::endl;

    EXPECT_GT(throughput, 10000); // At least 10k events/second
}

TEST_F(EventLoopTest, Statistics) {
    auto sub_id = event_loop->subscribe(EventType::CUSTOM,
        [](const Event& event) {
            // Do some work
            std::this_thread::sleep_for(std::chrono::microseconds(10));
        });

    EXPECT_TRUE(event_loop->start());

    // Reset statistics
    event_loop->reset_statistics();

    // Emit some events
    for (int i = 0; i < 100; ++i) {
        auto event = std::make_shared<Event>(EventType::CUSTOM);
        event_loop->emit(event);
    }

    // Wait for processing
    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    auto stats = event_loop->get_statistics();

    EXPECT_EQ(stats.events_processed, 100);
    EXPECT_GT(stats.average_latency_ns, 0);
    EXPECT_GT(stats.max_latency_ns, stats.average_latency_ns);

    std::cout << "Average latency: " << stats.average_latency_ns / 1000.0 << " μs" << std::endl;
    std::cout << "Max latency: " << stats.max_latency_ns / 1000.0 << " μs" << std::endl;
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
