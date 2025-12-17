"""
Application Service - Core business logic
"""
import json
import socket
from typing import Dict, Any
from ..domain import ServerInfo, SessionData, HealthStatus
from ..interfaces.cache_port import CachePort
from ..interfaces.web_port import WebPort

class AppService:
    def __init__(self, cache: CachePort):
        self.cache = cache
        self.server_info = ServerInfo.create(socket.gethostname())
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {
            "server_id": self.server_info.server_id,
            "hostname": self.server_info.hostname,
            "start_time": self.server_info.start_time
        }
    
    def handle_request(self, web: WebPort) -> Dict[str, Any]:
        """Handle incoming request with session management"""
        session_id = web.get_session_id()
        
        if not session_id:
            # Create new session
            session_data = SessionData.create({"visits": 1})
            session_id = session_data.session_id
            web.set_session_id(session_id)
        else:
            # Update existing session
            session_data = self._get_session(session_id)
            if session_data:
                session_data.user_data["visits"] += 1
            else:
                session_data = SessionData.create({"visits": 1})
        
        # Store session in cache
        self._store_session(session_id, session_data)
        
        return {
            "message": f"Hello from {self.server_info.server_id}",
            "session_id": session_id,
            "visits": session_data.user_data["visits"],
            "server_info": self.get_server_info()
        }
    
    def check_health(self) -> HealthStatus:
        """Check application and dependencies health"""
        try:
            if self.cache.ping():
                return HealthStatus.healthy("Application and Cache healthy.")
            else:
                return HealthStatus.unhealthy("Cache connection failed.")
        except Exception as e:
            return HealthStatus.unhealthy(f"Health check failed: {str(e)}")
    
    def _get_session(self, session_id: str) -> SessionData:
        """Get session from cache"""
        try:
            data = self.cache.get(f"session:{session_id}")
            if data:
                session_dict = json.loads(data)
                return SessionData(**session_dict)
        except Exception:
            pass
        return None
    
    def _store_session(self, session_id: str, session_data: SessionData) -> None:
        """Store session in cache"""
        try:
            data = json.dumps({
                "session_id": session_data.session_id,
                "user_data": session_data.user_data,
                "created_at": session_data.created_at
            })
            self.cache.set(f"session:{session_id}", data, ttl=3600)
        except Exception:
            pass
