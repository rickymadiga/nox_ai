# ui/utils/key_generator.py - NEW (Safe Key Generation)

import time
import hashlib
from typing import Any


class KeyGenerator:
    """Generate unique, safe keys for Streamlit elements."""
    
    _counter = 0
    _last_time = 0
    
    @classmethod
    def generate(cls, prefix: str = "element", data: Any = None) -> str:
        """
        Generate a unique key.
        
        Args:
            prefix: Prefix for the key
            data: Optional data to hash into the key
        
        Returns:
            Unique key string
        """
        # Use timestamp + counter for uniqueness
        current_time = time.time()
        
        # Reset counter if time changed
        if current_time > cls._last_time:
            cls._counter = 0
            cls._last_time = current_time
        else:
            cls._counter += 1
        
        # Build unique component
        unique_str = f"{current_time}_{cls._counter}"
        
        # Add hash of data if provided
        if data is not None:
            data_str = str(data)
            data_hash = hashlib.md5(data_str.encode()).hexdigest()[:8]
            unique_str += f"_{data_hash}"
        
        # Convert to valid Streamlit key (alphanumeric + underscore)
        timestamp_ms = int(current_time * 1000000)
        return f"{prefix}_{timestamp_ms}_{cls._counter}"
    
    @classmethod
    def download_key(cls, filename: str, index: int = 0) -> str:
        """Generate key for download button."""
        return cls.generate(f"download_{filename.replace('.', '_')}", index)
    
    @classmethod
    def button_key(cls, label: str, index: int = 0) -> str:
        """Generate key for button."""
        return cls.generate(f"btn_{label.replace(' ', '_').lower()}", index)