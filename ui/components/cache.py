from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import pickle

@dataclass
class CacheEntry:
    """Cache entry with expiration."""
    key: str
    value: Any
    created_at: datetime
    ttl: int  # seconds
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl)


class CacheManager:
    """Simple in-memory cache manager."""
    
    def __init__(self, max_size: int = 100, ttl: int = 600):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl = ttl
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set cache value."""
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            ttl=ttl or self.default_ttl
        )
        self.cache[key] = entry
    
    def get(self, key: str) -> Optional[Any]:
        """Get cache value."""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        if entry.is_expired():
            del self.cache[key]
            return None
        
        return entry.value
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None
    
    def delete(self, key: str):
        """Delete cache entry."""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """Clear all cache."""
        self.cache.clear()
    
    def _evict_oldest(self):
        """Evict oldest cache entry."""
        if not self.cache:
            return
        
        oldest_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].created_at
        )
        del self.cache[oldest_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "utilization": (len(self.cache) / self.max_size) * 100
        }