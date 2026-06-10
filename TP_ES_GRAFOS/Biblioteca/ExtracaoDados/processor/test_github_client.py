import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import patch, Mock
from pathlib import Path

from github_client import GitHubClient

class TestGitHubClient(unittest.TestCase):
    @patch("github_client.requests.post")
    def test_run_query_success(self, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": {"ok": True}}
        mock_post.return_value = mock_resp

        client = GitHubClient("token")
        payload = client.run_query("query")
        self.assertIn("data", payload)
        self.assertTrue(payload["data"]["ok"])

    @patch("github_client.requests.post")
    def test_run_query_http_error(self, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 401
        mock_resp.json.return_value = {"message": "Bad auth"}
        mock_post.return_value = mock_resp

        client = GitHubClient("token")
        with self.assertRaises(RuntimeError):
            client.run_query("query")

if __name__ == "__main__":
    unittest.main(verbosity=2)