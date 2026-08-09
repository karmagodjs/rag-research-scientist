"""
Unit tests for claim generation and dynamic confidence calculation.
"""

import unittest
from evidence.claims import ClaimGenerator


class TestClaims(unittest.TestCase):

    def setUp(self):
        self.generator = ClaimGenerator()

    def test_dynamic_confidence_score(self):
        # 3 sources, high relevance (0.9), recency 1.0, no contradiction
        score_high = self.generator._calculate_confidence(
            num_sources=3,
            avg_relevance=0.9,
            recency_score=1.0,
            has_contradiction=False
        )
        self.assertGreaterEqual(score_high, 0.8)

        # 1 source, low relevance (0.3), recency 0.5, with contradiction
        score_low = self.generator._calculate_confidence(
            num_sources=1,
            avg_relevance=0.3,
            recency_score=0.5,
            has_contradiction=True
        )
        self.assertLess(score_low, score_high)

    def test_claim_generation_from_evidence(self):
        evidence_items = [
            {
                "paper_id": "p1",
                "paper_title": "Paper 1",
                "snippet": "Transformer OCR outperforms traditional CNN baseline.",
                "source_url": "http://arxiv.org/abs/1",
                "relevance_score": 0.85,
                "published_year": "2025"
            }
        ]
        claims = self.generator.generate_claims(evidence_items)
        self.assertEqual(len(claims), 1)
        self.assertIn("confidence", claims[0])
        self.assertGreater(claims[0]["confidence"], 0.0)


if __name__ == "__main__":
    unittest.main()
