import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock

from issues_fetcher import IssuesFetcher

class TestIssuesFetcher(unittest.TestCase):
    def test_fetch_saves_chunks(self):
        tmpdir = Path(tempfile.mkdtemp())

        # two pages: first hasNextPage True, second False
        payload1 = {
            "data": {
                "repository": {
                    "issues": {
                        "nodes": [{"number": 1, "author": {"login": "a"}}],
                        "pageInfo": {"hasNextPage": True, "endCursor": "c1"}
                    }
                }
            }
        }
        payload2 = {
            "data": {
                "repository": {
                    "issues": {
                        "nodes": [{"number": 2, "author": {"login": "b"}}],
                        "pageInfo": {"hasNextPage": False}
                    }
                }
            }
        }

        client = Mock()
        client.run_query.side_effect = [payload1, payload2]

        fetcher = IssuesFetcher(client, "owner", "repo", tmpdir)
        fetcher.fetch()

        # final saved file should exist
        saved = list(tmpdir.glob("issues_*.json"))
        self.assertTrue(len(saved) >= 1)
        # verify content includes both nodes
        combined = []
        for p in saved:
            combined.extend(json.loads(p.read_text(encoding="utf-8")))
        nums = {item.get("number") for item in combined}
        self.assertIn(1, nums)
        self.assertIn(2, nums)

if __name__ == "__main__":
    unittest.main(verbosity=2)