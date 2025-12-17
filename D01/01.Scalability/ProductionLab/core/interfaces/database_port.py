"""
Database Port - Interface for database operations
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class DatabasePort(ABC):
    
    @abstractmethod
    def execute(self, query: str, params: tuple = None) -> None:
        """Execute a query without returning results"""
        pass
    
    @abstractmethod
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Fetch a single row"""
        pass
    
    @abstractmethod
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Fetch all rows"""
        pass
    
    @abstractmethod
    def insert(self, query: str, params: tuple = None) -> int:
        """Insert and return last insert id"""
        pass
    
    @abstractmethod
    def ping(self) -> bool:
        """Health check"""
        pass
