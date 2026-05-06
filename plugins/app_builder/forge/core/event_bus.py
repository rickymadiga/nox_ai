import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventBus:
    """
    🔥 Event Bus for agent communication
    Supports both Message objects and dict format
    """

    def __init__(self) -> None:
        """Initialize the event bus"""
        self.subscribers: Dict[str, List[Callable]] = {}
        print("[EventBus] Initialized")
        logger.info("[EventBus] Initialized")

    # ─────────────────────────────
    # SUBSCRIBE
    # ─────────────────────────────
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Subscribe to an event type
        
        Args:
            event_type: Type of event to subscribe to
            handler: Callback function (async or sync)
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        self.subscribers[event_type].append(handler)
        
        handler_name = getattr(handler, "__name__", "unknown")
        print(f"[EventBus] subscribed → {event_type} (handler: {handler_name})")
        logger.debug(f"[EventBus] subscribed → {event_type}")

    # ─────────────────────────────
    # PUBLISH
    # ─────────────────────────────
    async def publish(self, message: Any) -> None:
        """
        🔥 Publish a message to all subscribers
        
        Args:
            message: Message object or dict with message_type/type field
        """
        # 🔥 Extract message_type from Message object or dict
        message_type = None
        
        if isinstance(message, dict):
            # Try both "message_type" and "type" for dict
            message_type = message.get("message_type") or message.get("type")
        else:
            # Try Message object attributes
            message_type = getattr(message, "message_type", None)

        # Validate message_type
        if not message_type:
            print("[EventBus] ❌ Dropped message (no message_type)")
            logger.warning("[EventBus] Dropped message (no message_type)")
            return

        # Get handlers for this event type
        handlers = self.subscribers.get(message_type, [])

        print(f"[EventBus] Publishing {message_type} | handlers={len(handlers)}")
        logger.debug(f"[EventBus] Publishing {message_type} to {len(handlers)} handlers")

        # Call all handlers
        if handlers:
            for handler in handlers:
                try:
                    # 🔥 Support both async and sync handlers
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        handler(message)
                        
                except Exception as e:
                    handler_name = getattr(handler, "__name__", "unknown")
                    print(f"[EventBus ERROR] Handler {handler_name} failed: {type(e).__name__}: {e}")
                    logger.error(
                        f"[EventBus ERROR] Handler {handler_name} for {message_type}: {e}",
                        exc_info=True
                    )
        else:
            logger.debug(f"[EventBus] No handlers for {message_type}")

    # ─────────────────────────────
    # SAFE EXECUTION (OPTIONAL)
    # ─────────────────────────────
    async def _safe_execute(
        self,
        handler: Callable,
        message: Any,
        agent_name: str = "unknown"
    ) -> None:
        """
        Safely execute a handler with error handling
        
        Args:
            handler: Handler function to execute
            message: Message to pass to handler
            agent_name: Name of agent for logging
        """
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(message)
            else:
                handler(message)
                
        except Exception as e:
            error_type = type(e).__name__
            print(f"[EventBus ERROR] agent={agent_name} | {error_type}: {e}")
            logger.error(
                f"[EventBus ERROR] agent={agent_name} | {error_type}: {e}",
                exc_info=True
            )

    # ─────────────────────────────
    # UNSUBSCRIBE
    # ─────────────────────────────
    def unsubscribe(self, event_type: str, handler: Callable) -> bool:
        """
        Unsubscribe from an event
        
        Args:
            event_type: Type of event
            handler: Handler to remove
        
        Returns:
            True if handler was found and removed
        """
        if event_type in self.subscribers:
            if handler in self.subscribers[event_type]:
                self.subscribers[event_type].remove(handler)
                handler_name = getattr(handler, "__name__", "unknown")
                print(f"[EventBus] unsubscribed → {event_type} (handler: {handler_name})")
                logger.debug(f"[EventBus] unsubscribed → {event_type}")
                return True
        return False

    # ─────────────────────────────
    # UNSUBSCRIBE ALL
    # ─────────────────────────────
    def clear_subscribers(self, event_type: Optional[str] = None) -> None:
        """
        Clear subscribers for an event type or all events
        
        Args:
            event_type: Specific event to clear, or None for all
        """
        if event_type:
            if event_type in self.subscribers:
                self.subscribers[event_type] = []
                print(f"[EventBus] Cleared subscribers for {event_type}")
                logger.debug(f"[EventBus] Cleared subscribers for {event_type}")
        else:
            self.subscribers.clear()
            print("[EventBus] Cleared all subscribers")
            logger.debug("[EventBus] Cleared all subscribers")

    # ─────────────────────────────
    # DEBUG/STATS
    # ─────────────────────────────
    def stats(self) -> None:
        """Print subscriber statistics"""
        print("\n[EventBus] Subscriber Map")
        print("=" * 50)
        
        if not self.subscribers:
            print("  (no subscribers)")
        else:
            for event_type, handlers in self.subscribers.items():
                handler_names = []
                for h in handlers:
                    # Try to get agent name from handler
                    if hasattr(h, "__self__"):
                        agent_name = getattr(h.__self__, "name", "unknown")
                    else:
                        agent_name = getattr(h, "__name__", "unknown")
                    handler_names.append(agent_name)
                
                handler_str = ", ".join(handler_names)
                print(f"  {event_type:20} → {handler_str}")

        print("=" * 50)
        print()

    def get_subscriber_count(self, event_type: Optional[str] = None) -> int:
        """
        Get number of subscribers
        
        Args:
            event_type: Specific event type, or None for total
        
        Returns:
            Number of subscribers
        """
        if event_type:
            return len(self.subscribers.get(event_type, []))
        else:
            return sum(len(handlers) for handlers in self.subscribers.values())

    def get_event_types(self) -> List[str]:
        """Get list of all event types with subscribers"""
        return list(self.subscribers.keys())

    def __repr__(self) -> str:
        """String representation"""
        total_subscribers = self.get_subscriber_count()
        event_count = len(self.subscribers)
        return f"<EventBus events={event_count} subscribers={total_subscribers}>"