import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from core.services.app_service import AppService
from infrastructure.cache.memory_adapter import MemoryAdapter
from tests.unit.mocks import MockWebAdapter

class TestCoreLogic(unittest.TestCase):
    def setUp(self):
        self.cache = MemoryAdapter()
        self.app_service = AppService(self.cache)
        self.web = MockWebAdapter()
    
    def test_server_info(self):
        info = self.app_service.get_server_info()
        
        self.assertIn("server_id", info)
        self.assertIn("hostname", info)
        self.assertIn("start_time", info)
    
    def test_new_session_request(self):
        self.web._session_id = None
        
        result = self.app_service.handle_request(self.web)
        
        self.assertEqual(result["visits"], 1)
        self.assertIsNotNone(self.web._session_id)
    
    def test_health_check_success(self):
        health = self.app_service.check_health()
        
        self.assertEqual(health.status, "healthy")
    
    def test_health_check_cache_failure(self):
        # Use failing cache
        from tests.unit.mocks import MockCacheAdapter
        failing_cache = MockCacheAdapter(should_fail=True)
        app_service = AppService(failing_cache)
        
        health = app_service.check_health()
        
        self.assertEqual(health.status, "unhealthy")

if __name__ == '__main__':
    unittest.main()
