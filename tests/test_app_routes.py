import unittest
from fastapi.testclient import TestClient

from backend.app import app


class AppRoutesTests(unittest.TestCase):
    def test_root_endpoint_returns_info(self):
        client = TestClient(app)
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Grand Canyon", response.text)


if __name__ == "__main__":
    unittest.main()
