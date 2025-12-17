import unittest
import time
from core.domain.models import ServerInfo, SessionData, HealthStatus

class TestServerInfo(unittest.TestCase):
    def test_create_server_info(self):
        server = ServerInfo.create("test-host")
        
        self.assertIsNotNone(server.server_id)
        self.assertEqual(server.hostname, "test-host")
        self.assertIsInstance(server.start_time, float)

class TestSessionData(unittest.TestCase):
    def test_create_session_data(self):
        user_data = {"visits": 1}
        session = SessionData.create(user_data)
        
        self.assertIsNotNone(session.session_id)
        self.assertEqual(session.user_data, user_data)
        self.assertIsInstance(session.created_at, float)

class TestHealthStatus(unittest.TestCase):
    def test_healthy_status(self):
        health = HealthStatus.healthy("All good")
        
        self.assertEqual(health.status, "healthy")
        self.assertEqual(health.message, "All good")
        self.assertIsInstance(health.timestamp, float)
    
    def test_unhealthy_status(self):
        health = HealthStatus.unhealthy("Error occurred")
        
        self.assertEqual(health.status, "unhealthy")
        self.assertEqual(health.message, "Error occurred")
        self.assertIsInstance(health.timestamp, float)

if __name__ == '__main__':
    unittest.main()
