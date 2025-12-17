"""
Web Port - Interface for web framework operations
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class WebPort(ABC):
    
    @abstractmethod
    def get_request_data(self) -> Dict[str, Any]:
        """Get current request data"""
        pass
    
    @abstractmethod
    def get_session_id(self) -> Optional[str]:
        """Get session ID from request"""
        pass
    
    @abstractmethod
    def set_session_id(self, session_id: str) -> None:
        """Set session ID in response"""
        pass
    
    @abstractmethod
    def create_response(self, data: Dict[str, Any], status_code: int = 200) -> Any:
        """Create HTTP response"""
        pass
