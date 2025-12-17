from typing import Optional, Dict
from core.interfaces.cache_port import CachePort
from core.interfaces.web_port import WebPort

class MockCacheAdapter(CachePort):
    def __init__(self, should_fail=False):
        self._store = {}
        self._should_fail = should_fail
    
    def get(self, key: str) -> Optional[str]:
        if self._should_fail:
            raise Exception("Cache error")
        return self._store.get(key)
    
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        if self._should_fail:
            return False
        self._store[key] = value
        return True
    
    def delete(self, key: str) -> bool:
        if self._should_fail:
            return False
        return self._store.pop(key, None) is not None
    
    def exists(self, key: str) -> bool:
        if self._should_fail:
            return False
        return key in self._store
    
    def ping(self) -> bool:
        return not self._should_fail

class MockWebAdapter(WebPort):
    def __init__(self):
        self._session_id = None
        self._request_data = {}
        self._response_data = None
    
    def get_request_data(self) -> Dict:
        return self._request_data
    
    def get_session_id(self) -> Optional[str]:
        return self._session_id
    
    def set_session_id(self, session_id: str) -> None:
        self._session_id = session_id
    
    def create_response(self, data: Dict, status_code: int = 200):
        self._response_data = {"data": data, "status": status_code}
        return self._response_data
