"""
Unit tests for PersistentStorage and Vercel/Local Server API routes.
"""

import unittest
import json
from storage import storage, PersistentStorage


class TestStorageAndAPI(unittest.TestCase):

    def test_storage_save_and_get(self):
        test_id = "res_test_123"
        test_data = {
            "id": test_id,
            "research_question": "Test query",
            "claims": [{"claim": "Test claim"}]
        }
        storage.save(test_id, test_data)
        retrieved = storage.get(test_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["id"], test_id)
        self.assertEqual(retrieved["research_question"], "Test query")


if __name__ == "__main__":
    unittest.main()
