"""
Unit tests for retrieval modules (arXiv, web, deduplication, decomposition).
"""

import unittest
from retrieval.base import Document
from retrieval.dedup import DocumentDeduplicator
from retrieval.decomposer import QueryDecomposer


class TestRetrieval(unittest.TestCase):

    def test_deduplication_exact_doi(self):
        dedup = DocumentDeduplicator()
        docs = [
            Document(id="d1", title="Paper A", authors=["A"], abstract="abs", url="u1", published="2025", source="s1", doi="10.1234/5678"),
            Document(id="d2", title="Paper A Dup", authors=["B"], abstract="abs", url="u2", published="2025", source="s2", doi="10.1234/5678"),
        ]
        result = dedup.deduplicate(docs)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "d1")

    def test_deduplication_title_similarity(self):
        dedup = DocumentDeduplicator(title_similarity_threshold=0.8)
        docs = [
            Document(id="d1", title="OCR for Low Resource Indic Languages", authors=["A"], abstract="abs", url="u1", published="2025", source="s1"),
            Document(id="d2", title="OCR for Low Resource Indic Languages Study", authors=["B"], abstract="abs", url="u2", published="2025", source="s2"),
        ]
        result = dedup.deduplicate(docs)
        self.assertEqual(len(result), 1)

    def test_query_decomposition(self):
        decomposer = QueryDecomposer()
        subqueries = decomposer.decompose("OCR on low-resource Indic languages since 2024")
        self.assertGreater(len(subqueries), 1)

    def test_query_decomposition_domain_agnostic(self):
        decomposer = QueryDecomposer()
        bio_subqueries = decomposer.decompose("protein folding")
        self.assertTrue(any("methods" in sq or "benchmark" in sq for sq in bio_subqueries))
        self.assertFalse(any("biography" in sq for sq in bio_subqueries))

        interp_subqueries = decomposer.decompose("transformer interpretability")
        self.assertTrue(any("evaluation" in sq or "empirical" in sq for sq in interp_subqueries))


if __name__ == "__main__":
    unittest.main()

