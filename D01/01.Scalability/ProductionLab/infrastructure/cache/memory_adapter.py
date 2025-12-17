"""
Memory Adapter - In-memory implementation of CachePort (for testing/fallback)
"""
import time
from typing import Optional, Dict, Tuple
from core.interfaces.cache_port import CachePort

class MemoryAdapter(CachePort):
    def __init__(self):
        self._store: Dict[str, Tuple[str, Optional[float]]] = {}
    
    def get(self, key: str) -> Optional[str]:
        if key in self._store:
            value, expiry = self._store[key]
            if expiry is None or time.time() < expiry:
                return value
            else:
                del self._store[key]
        return None
    
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        expiry = time.time() + ttl if ttl else None
        self._store[key] = (value, expiry)
        return True
    
    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        return self.get(key) is not None
    
    def ping(self) -> bool:
        return True
