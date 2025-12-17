import unittest
import time
from infrastructure.cache.memory_adapter import MemoryAdapter

class TestMemoryAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = MemoryAdapter()
    
    def test_set_and_get(self):
        self.assertTrue(self.adapter.set("key1", "value1"))
        self.assertEqual(self.adapter.get("key1"), "value1")
    
    def test_get_nonexistent_key(self):
        self.assertIsNone(self.adapter.get("nonexistent"))
    
    def test_set_with_ttl(self):
        self.assertTrue(self.adapter.set("key2", "value2", ttl=1))
        self.assertEqual(self.adapter.get("key2"), "value2")
        
        # Wait for expiry
        time.sleep(1.1)
        self.assertIsNone(self.adapter.get("key2"))
    
    def test_delete(self):
        self.adapter.set("key3", "value3")
        self.assertTrue(self.adapter.delete("key3"))
        self.assertIsNone(self.adapter.get("key3"))
        
        # Delete non-existent key
        self.assertFalse(self.adapter.delete("nonexistent"))
    
    def test_exists(self):
        self.adapter.set("key4", "value4")
        self.assertTrue(self.adapter.exists("key4"))
        self.assertFalse(self.adapter.exists("nonexistent"))
    
    def test_ping(self):
        self.assertTrue(self.adapter.ping())

if __name__ == '__main__':
    unittest.main()
