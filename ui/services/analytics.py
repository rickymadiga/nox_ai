from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List
import json
from pathlib import Path

@dataclass
class AnalyticsEvent:
    """Analytics event data structure."""
    event_type: str
    success: bool
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    intent: str = ""
    action: str = ""


class AnalyticsService:
    """Centralized analytics tracking service."""
    
    def __init__(self, storage_path: str = "analytics"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.events: List[AnalyticsEvent] = []
    
    def track_event(self, event: AnalyticsEvent):
        """Track an analytics event."""
        self.events.append(event)
        self._persist_event(event)
    
    def _persist_event(self, event: AnalyticsEvent):
        """Persist event to disk."""
        try:
            file_path = self.storage_path / f"events_{datetime.now().strftime('%Y%m%d')}.jsonl"
            
            event_dict = {
                "event_type": event.event_type,
                "intent": event.intent,
                "action": event.action,
                "success": event.success,
                "timestamp": event.timestamp.isoformat(),
                "metadata": event.metadata
            }
            
            with open(file_path, "a") as f:
                f.write(json.dumps(event_dict) + "\n")
        except Exception as e:
            print(f"Failed to persist analytics event: {e}")
    
    def get_events(self, event_type: str = None) -> List[AnalyticsEvent]:
        """Get events by type."""
        if event_type:
            return [e for e in self.events if e.event_type == event_type]
        return self.events
    
    def get_intent_stats(self, intent: str) -> Dict[str, Any]:
        """Get statistics for specific intent."""
        intent_events = [e for e in self.events if e.intent == intent]
        
        if not intent_events:
            return {}
        
        success_count = sum(1 for e in intent_events if e.success)
        
        return {
            "total_executions": len(intent_events),
            "successful_executions": success_count,
            "failed_executions": len(intent_events) - success_count,
            "success_rate": (success_count / len(intent_events)) * 100,
            "last_executed": max(e.timestamp for e in intent_events)
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get comprehensive analytics."""
        total_events = len(self.events)
        successful_events = sum(1 for e in self.events if e.success)
        
        return {
            "total_events": total_events,
            "successful_events": successful_events,
            "failed_events": total_events - successful_events,
            "success_rate": (successful_events / total_events * 100) if total_events > 0 else 0,
            "unique_intents": len(set(e.intent for e in self.events if e.intent))
        }