"""
Session Models - Session data for request tracking
"""
from dataclasses import dataclass
import uuid
import time


@dataclass
class SessionData:
    session_id: str
    user_data: dict
    created_at: float
    
    @classmethod
    def create(cls, user_data: dict) -> 'SessionData':
        return cls(
            session_id=str(uuid.uuid4()),
            user_data=user_data,
            created_at=time.time()
        )
