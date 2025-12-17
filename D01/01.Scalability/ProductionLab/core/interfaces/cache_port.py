"""
Cache Port - Interface for cache operations
"""
from abc import ABC, abstractmethod
from typing import Optional, Any

class CachePort(ABC):
    
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set key-value with optional TTL"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
    
    @abstractmethod
    def ping(self) -> bool:
        """Health check"""
        pass
