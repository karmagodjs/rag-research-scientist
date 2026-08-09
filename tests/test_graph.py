"""
Unit tests for evidence graph construction and NetworkX compatibility.
"""

import unittest
from evidence.graph import EvidenceGraph
from retrieval.base import Document


class TestGraph(unittest.TestCase):

    def test_evidence_graph_building(self):
        graph = EvidenceGraph()
        query = "OCR on low-resource Indic languages"
        docs = [Document(id="p1", title="Paper 1", authors=["A"], abstract="abs", url="http://url.com", published="2025", source="arxiv")]
        claims = [
            {
                "claim": "Claim A",
                "confidence": 0.8,
                "evidence": [{"snippet": "Snippet A", "source_url": "http://url.com", "paper_id": "p1"}]
            }
        ]
        contradictions = []

        g_data = graph.build_graph(query, claims, contradictions, docs)
        self.assertIn("nodes", g_data)
        self.assertIn("edges", g_data)
        self.assertGreater(len(g_data["nodes"]), 0)
        self.assertGreater(len(g_data["edges"]), 0)


if __name__ == "__main__":
    unittest.main()
