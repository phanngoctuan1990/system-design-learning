"""
Server Models - Server info and health status
"""
from dataclasses import dataclass
import uuid
import time
import os


@dataclass
class ServerInfo:
    server_id: str
    hostname: str
    start_time: float
    
    @classmethod
    def create(cls, hostname: str) -> 'ServerInfo':
        # Use SERVER_ID from env if available, otherwise generate uuid
        server_id = os.getenv('SERVER_ID', str(uuid.uuid4())[:8])
        return cls(
            server_id=server_id,
            hostname=hostname,
            start_time=time.time()
        )


@dataclass
class HealthStatus:
    status: str
    message: str
    timestamp: float
    
    @classmethod
    def healthy(cls, message: str = "OK") -> 'HealthStatus':
        return cls("healthy", message, time.time())
    
    @classmethod
    def unhealthy(cls, message: str = "Error") -> 'HealthStatus':
        return cls("unhealthy", message, time.time())
