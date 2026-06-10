import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock

from pr_fetcher import PRFetcher

class TestPRFetcher(unittest.TestCase):
    def test_fetch_saves_chunks(self):
        tmpdir = Path(tempfile.mkdtemp())

        payload1 = {
            "data": {
                "repository": {
                    "pullRequests": {
                        "nodes": [{"number": 10, "author": {"login": "x"}}],
                        "pageInfo": {"hasNextPage": True, "endCursor": "c1"}
                    }
                }
            }
        }
        payload2 = {
            "data": {
                "repository": {
                    "pullRequests": {
                        "nodes": [{"number": 11, "author": {"login": "y"}}],
                        "pageInfo": {"hasNextPage": False}
                    }
                }
            }
        }

        client = Mock()
        client.run_query.side_effect = [payload1, payload2]

        fetcher = PRFetcher(client, "owner", "repo", tmpdir)
        fetcher.fetch()

        saved = list(tmpdir.glob("pull_requests_*.json"))
        self.assertTrue(len(saved) >= 1)
        combined = []
        for p in saved:
            combined.extend(json.loads(p.read_text(encoding="utf-8")))
        nums = {item.get("number") for item in combined}
        self.assertIn(10, nums)
        self.assertIn(11, nums)

if __name__ == "__main__":
    unittest.main(verbosity=2)