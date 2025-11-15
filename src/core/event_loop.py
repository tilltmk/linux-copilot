"""
Event Loop - Central event-driven architecture for the Linux Copilot
Handles async operations, event dispatching, and subscriber management
"""

import asyncio
import logging
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import threading


class EventPriority(Enum):
    """Priority levels for event processing"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Event:
    """Base event class for all system events"""
    event_type: str
    data: Dict[str, Any]
    priority: EventPriority = EventPriority.NORMAL
    timestamp: float = 0.0
    source: Optional[str] = None

    def __post_init__(self):
        if self.timestamp == 0.0:
            import time
            self.timestamp = time.time()


class EventLoop:
    """
    Central event loop for the Linux Copilot system

    Features:
    - Async event processing
    - Priority-based event queue
    - Thread-safe event emission
    - Subscriber management
    - Graceful shutdown handling
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._tasks: List[asyncio.Task] = []
        self._lock = threading.Lock()

    async def start(self):
        """Start the event loop"""
        if self._running:
            self.logger.warning("Event loop already running")
            return

        self._running = True
        self._loop = asyncio.get_running_loop()
        self.logger.info("Event loop started")

        # Start event processor task
        processor_task = asyncio.create_task(self._process_events())
        self._tasks.append(processor_task)

    async def stop(self):
        """Stop the event loop gracefully"""
        if not self._running:
            return

        self.logger.info("Stopping event loop...")
        self._running = False

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        self.logger.info("Event loop stopped")

    def subscribe(self, event_type: str, callback: Callable):
        """
        Subscribe to an event type

        Args:
            event_type: Type of event to subscribe to
            callback: Async or sync callback function to call when event occurs
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []

            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
                self.logger.debug(f"Subscribed to {event_type}: {callback.__name__}")

    def unsubscribe(self, event_type: str, callback: Callable):
        """
        Unsubscribe from an event type

        Args:
            event_type: Type of event to unsubscribe from
            callback: Callback function to remove
        """
        with self._lock:
            if event_type in self._subscribers:
                if callback in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(callback)
                    self.logger.debug(f"Unsubscribed from {event_type}: {callback.__name__}")

    def emit(self, event: Event):
        """
        Emit an event (thread-safe)

        Args:
            event: Event to emit
        """
        if not self._running:
            self.logger.warning("Cannot emit event - event loop not running")
            return

        # Priority queue uses tuples: (priority, counter, item)
        # Lower priority value = higher priority
        priority_value = -event.priority.value  # Negate for correct ordering

        # Use thread-safe call
        if self._loop:
            asyncio.run_coroutine_threadsafe(
                self._event_queue.put((priority_value, event)),
                self._loop
            )

    async def _process_events(self):
        """Process events from the queue"""
        self.logger.info("Event processor started")

        while self._running:
            try:
                # Wait for event with timeout to allow checking _running flag
                try:
                    priority, event = await asyncio.wait_for(
                        self._event_queue.get(),
                        timeout=0.5
                    )
                except asyncio.TimeoutError:
                    continue

                # Get subscribers for this event type
                with self._lock:
                    subscribers = self._subscribers.get(event.event_type, []).copy()

                # Call all subscribers
                for callback in subscribers:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event)
                        else:
                            # Run sync callback in executor to avoid blocking
                            await self._loop.run_in_executor(None, callback, event)
                    except Exception as e:
                        self.logger.error(
                            f"Error in event handler {callback.__name__} "
                            f"for event {event.event_type}: {e}",
                            exc_info=True
                        )

            except Exception as e:
                self.logger.error(f"Error processing event: {e}", exc_info=True)

        self.logger.info("Event processor stopped")

    async def run_forever(self):
        """Run the event loop until stop() is called"""
        await self.start()

        try:
            while self._running:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        finally:
            await self.stop()
