
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


    def test_exact_paper_query_detection_and_ranking(self):
        from retrieval.query_utils import detect_exact_paper_query
        from ranking.reranker import Reranker


        is_exact, title, author = detect_exact_paper_query("Attention Is All You Need")
        self.assertTrue(is_exact)
        self.assertEqual(title, "attention is all you need")


        is_exact, title, author = detect_exact_paper_query("Attention Is All You Need paper")
        self.assertTrue(is_exact)
        self.assertEqual(title, "attention is all you need")


        is_exact, title, author = detect_exact_paper_query("Vaswani Attention Is All You Need")
        self.assertTrue(is_exact)
        self.assertEqual(author, "vaswani")


        is_exact, title, author = detect_exact_paper_query("recent transformer attention research")
        self.assertFalse(is_exact)


        is_exact, title, author = detect_exact_paper_query("papers about attention mechanisms")
        self.assertFalse(is_exact)


        reranker = Reranker()
        docs = [
            Document(id="d1", title="Survey of Attention Mechanisms", authors=["A. Smith"], abstract="General survey of attention in deep learning.", url="u1", published="2024", source="s1"),
            Document(id="d2", title="Attention Is All You Need", authors=["Ashish Vaswani", "Noam Shazeer"], abstract="We propose the Transformer, a novel architecture.", url="u2", published="2017", source="arXiv"),
            Document(id="d3", title="Efficient Attention Models for Vision", authors=["B. Jones"], abstract="Optimized attention mechanisms for vision models.", url="u3", published="2023", source="s3"),
        ]
        ranked = reranker.rerank("Attention Is All You Need paper", docs)
        self.assertEqual(ranked[0].title, "Attention Is All You Need")

    def test_exact_title_failure_fallback_does_not_crash(self):
        from ranking.reranker import Reranker
        from agent import ResearchAgent


        reranker = Reranker()
        malformed_docs = [
            Document(id="m1", title="", authors=None, abstract=None, url="u1", published="2025", source="s1"),
            Document(id="m2", title="Attention Is All You Need", authors=["Ashish Vaswani"], abstract="Transformer paper.", url="u2", published="2017", source="arXiv")
        ]
        ranked = reranker.rerank("Attention Is All You Need", malformed_docs)
        self.assertTrue(len(ranked) > 0)
        self.assertEqual(ranked[0].title, "Attention Is All You Need")


        agent = ResearchAgent()
        report_exact = agent.run("Attention Is All You Need")
        self.assertIsNotNone(report_exact)
        self.assertIn("citation_list", report_exact)

        report_broad = agent.run("recent research on transformer attention mechanisms")
        self.assertIsNotNone(report_broad)
        self.assertIn("citation_list", report_broad)

    def test_arxiv_429_rate_limit_fallback(self):
        from unittest.mock import MagicMock, patch
        from retrieval.arxiv import ArxivRetriever

        retriever = ArxivRetriever()
        mock_resp = MagicMock()
        mock_resp.status_code = 429

        with patch("requests.get", return_value=mock_resp):
            docs = retriever.search("BERT")
            self.assertEqual(docs, [])

    def test_future_exception_and_timeout_isolation(self):
        from agent import ResearchAgent
        from retrieval.base import Document

        agent = ResearchAgent()
        def failing_search(query, top_k=3):
            raise RuntimeError("Network cable unplugged")

        agent.arxiv_retriever.search = failing_search

        report = agent.run("BERT")
        self.assertIsNotNone(report)
        self.assertIn("citation_list", report)
        self.assertNotEqual(report.get("status"), "HTTP 500")


if __name__ == "__main__":
    unittest.main()

