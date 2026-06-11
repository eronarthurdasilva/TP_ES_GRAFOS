import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import unittest
import tempfile
import json
from pathlib import Path

from interaction_parser import InteractionParser

class TestInteractionParser(unittest.TestCase):
    def setUp(self):
        self.tmp_brutos = Path(tempfile.mkdtemp())
        self.tmp_proc = Path(tempfile.mkdtemp())

        # issues: one issue with a comment by bob and closed by charlie
        issues = [
            {
                "author": {"login": "alice"},
                "state": "CLOSED",
                "comments": {
                    "nodes": [
                        {"author": {"login": "bob"}, "createdAt": "2023-01-01T00:00:00Z"}
                    ]
                },
                "timelineItems": {
                    "nodes": [
                        {
                            # ClosedEvent with Commit closer
                            "closer": {
                                "__typename": "Commit",
                                "author": {
                                    "user": {"login": "charlie"},
                                    "name": "Charlie Name"
                                }
                            }
                        }
                    ]
                }
            }
        ]

        # pull requests: one PR with comment by eve, review by frank (APPROVED), merged by george
        prs = [
            {
                "author": {"login": "dave"},
                "comments": {
                    "nodes": [
                        {"author": {"login": "eve"}, "createdAt": "2023-01-02T00:00:00Z"}
                    ]
                },
                "reviews": {
                    "nodes": [
                        {"author": {"login": "frank"}, "state": "APPROVED"}
                    ]
                },
                "mergedBy": {"login": "george"}
            }
        ]

        # write sample files
        with (self.tmp_brutos / "issues_1.json").open("w", encoding="utf-8") as f:
            json.dump(issues, f, ensure_ascii=False, indent=2)
        with (self.tmp_brutos / "pull_requests_1.json").open("w", encoding="utf-8") as f:
            json.dump(prs, f, ensure_ascii=False, indent=2)

    def tearDown(self):
        pass

    def test_parse_creates_expected_outputs(self):
        parser = InteractionParser(self.tmp_brutos, self.tmp_proc)
        parser.parse()

        comentarios_path = self.tmp_proc / "comentarios.json"
        fechamentos_path = self.tmp_proc / "fechamentos.json"
        reviews_path = self.tmp_proc / "reviews_merges.json"

        self.assertTrue(comentarios_path.exists())
        self.assertTrue(fechamentos_path.exists())
        self.assertTrue(reviews_path.exists())

        comentarios = json.loads(comentarios_path.read_text(encoding="utf-8"))
        fechamentos = json.loads(fechamentos_path.read_text(encoding="utf-8"))
        reviews = json.loads(reviews_path.read_text(encoding="utf-8"))

        # comentários: bob -> alice (issue), eve -> dave (pr) => 2 entries
        self.assertEqual(len(comentarios), 2)
        self.assertTrue(any(c["de"] == "bob" and c["para"] == "alice" and c["tipo"] == "comentario_issue" for c in comentarios))
        self.assertTrue(any(c["de"] == "eve" and c["para"] == "dave" and c["tipo"] == "comentario_pr" for c in comentarios))

        # fechamentos: charlie -> alice (commit closer) => 1 entry
        self.assertEqual(len(fechamentos), 1)
        self.assertEqual(fechamentos[0]["de"], "charlie")
        self.assertEqual(fechamentos[0]["para"], "alice")
        self.assertEqual(fechamentos[0]["tipo"], "fechamento")

        # reviews/merges: frank -> dave (aprovacao), george -> dave (merge) => 2 entries
        self.assertEqual(len(reviews), 2)
        self.assertTrue(any(r["de"] == "frank" and r["tipo"] == "aprovacao" for r in reviews))
        self.assertTrue(any(r["de"] == "george" and r["tipo"] == "merge" for r in reviews))


if __name__ == "__main__":
    unittest.main(verbosity=2)