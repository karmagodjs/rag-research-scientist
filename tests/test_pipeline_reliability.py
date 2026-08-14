import unittest
from unittest.mock import MagicMock, patch
from retrieval.base import Document
from retrieval.arxiv import ArxivRetriever
from retrieval.semantic import SemanticRetriever
from retrieval.dedup import DocumentDeduplicator
from ranking.reranker import Reranker
from evidence.extractor import EvidenceExtractor
from evidence.claims import ClaimGenerator
from evidence.contradiction import ContradictionDetector
from synthesis.gaps import ResearchGapAnalyzer
from agent import ResearchAgent, AgentConfig


class TestPipelineReliability(unittest.TestCase):

    def test_canonical_papers_not_injected_in_unrelated_queries(self):
        agent = ResearchAgent(config=AgentConfig(timeout_seconds=2))
        
        # Mock retrieval to return only a specific paper
        mock_docs = [
            Document(
                id="doc_bio_1",
                title="CRISPR Cas9 Gene Editing in Arabidopsis",
                authors=["J. Doe"],
                abstract="A study on plant gene editing using CRISPR systems.",
                url="https://example.com/crispr",
                published="2024",
                source="test"
            )
        ]
        agent.arxiv_retriever.search = MagicMock(return_value=mock_docs)
        agent.web_retriever.search = MagicMock(return_value=[])

        report = agent.run("CRISPR gene editing in plants")
        retrieved_titles = [doc["title"] for doc in report.get("citation_list", [])]

        self.assertIn("CRISPR Cas9 Gene Editing in Arabidopsis", retrieved_titles)
        self.assertNotIn("Attention Is All You Need", retrieved_titles)
        self.assertNotIn("BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding", retrieved_titles)
        self.assertNotIn("Deep Residual Learning for Image Recognition", retrieved_titles)

    def test_semantic_retrieval_integration(self):
        semantic_retriever = SemanticRetriever()
        docs = [
            Document(id="d1", title="Quantum Computing Advances", authors=["A"], abstract="Superconducting qubits", url="http://1", published="2024", source="test"),
            Document(id="d2", title="Protein Structure Prediction", authors=["B"], abstract="AlphaFold and structural biology", url="http://2", published="2024", source="test"),
        ]
        semantic_retriever.set_corpus(docs)
        results = semantic_retriever.search("Quantum Computing", top_k=2)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].id, "d1")
        self.assertIn("semantic_score", results[0].metadata)
        self.assertGreater(results[0].metadata["semantic_score"], 0.0)

    def test_arxiv_uses_instance_api_url_and_handles_429(self):
        custom_url = "https://custom.arxiv.endpoint/api/query"
        retriever = ArxivRetriever(api_url=custom_url, timeout=3)
        self.assertEqual(retriever.api_url, custom_url)

        # Mock 429 response
        mock_429 = MagicMock()
        mock_429.status_code = 429
        with patch("requests.get", return_value=mock_429) as mock_get:
            docs = retriever.search("Transformer")
            self.assertEqual(docs, [])
            mock_get.assert_called()
            # Verify custom URL was used in requests.get
            self.assertEqual(mock_get.call_args[0][0], custom_url)

    def test_exact_title_retrieval_ranking(self):
        reranker = Reranker()
        docs = [
            Document(id="d1", title="A Study of Attention Models in NLP", authors=["Author A"], abstract="Attention model analysis.", url="http://1", published="2022", source="arXiv"),
            Document(id="d2", title="Attention Is All You Need", authors=["Ashish Vaswani"], abstract="We propose Transformer.", url="http://2", published="2017", source="arXiv"),
            Document(id="d3", title="Beyond Attention Mechanisms", authors=["Author B"], abstract="Other architectures.", url="http://3", published="2023", source="arXiv"),
        ]
        ranked = reranker.rerank("Attention Is All You Need", docs)
        self.assertEqual(ranked[0].title, "Attention Is All You Need")
        self.assertGreater(ranked[0].metadata["final_score"], 100.0)

        # Also test BERT title matching
        bert_docs = [
            Document(id="b1", title="Evaluating Language Models", authors=["A"], abstract="Language model benchmarks.", url="http://1", published="2021", source="arXiv"),
            Document(id="b2", title="BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding", authors=["Jacob Devlin"], abstract="BERT paper.", url="http://2", published="2018", source="arXiv"),
        ]
        ranked_bert = reranker.rerank("BERT", bert_docs)
        self.assertEqual(ranked_bert[0].title, "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding")

    def test_contradiction_states(self):
        detector = ContradictionDetector()
        
        claim_support = {
            "claim": "RAG reduces factual hallucinations in large language models",
            "evidence": [{"paper_id": "p1", "snippet": "RAG significantly reduces hallucinations and improves accuracy.", "source_url": "http://1"}]
        }
        all_ev_support = [
            {"paper_id": "p1", "snippet": "RAG significantly reduces hallucinations and improves accuracy.", "source_url": "http://1", "relevance_score": 0.9}
        ]
        res_support = detector.analyze_claim(claim_support, all_ev_support)
        self.assertEqual(res_support["status"], "SUPPORTED")

        # Mixed / Challenge evidence
        all_ev_mixed = [
            {"paper_id": "p1", "snippet": "RAG significantly reduces hallucinations and improves accuracy.", "source_url": "http://1", "relevance_score": 0.9},
            {"paper_id": "p2", "snippet": "Our empirical study shows that RAG fails to reduce error rates under noisy retrieved contexts.", "source_url": "http://2", "relevance_score": 0.85}
        ]
        res_mixed = detector.analyze_claim(claim_support, all_ev_mixed)
        self.assertEqual(res_mixed["status"], "MIXED")

        # Insufficient evidence
        res_insufficient = detector.analyze_claim({"claim": "Quantum annealing optimizes RAG routing"}, [])
        self.assertEqual(res_insufficient["status"], "INSUFFICIENT")

    def test_no_unsupported_research_gaps(self):
        analyzer = ResearchGapAnalyzer()
        
        # Snippets with no limitations/challenges
        clean_evidence = [
            {
                "paper_id": "p1",
                "paper_title": "Efficient Matrix Multiplication",
                "snippet": "We achieve asymptotic speedups for large dense matrices on GPUs.",
                "source_url": "http://example.com/1",
                "relevance_score": 0.9
            }
        ]
        gaps = analyzer.detect_gaps(clean_evidence)
        self.assertEqual(len(gaps), 0)

        proposals = analyzer.propose_next_research(gaps, {})
        self.assertEqual(len(proposals), 0)

        # Snippets with explicit limitations
        limitation_evidence = [
            {
                "paper_id": "p2",
                "paper_title": "Vision Language Models",
                "snippet": "A major bottleneck is the severe scarcity of annotated paired data in low-resource languages.",
                "source_url": "http://example.com/2",
                "relevance_score": 0.95
            }
        ]
        gaps_with_lim = analyzer.detect_gaps(limitation_evidence)
        self.assertGreater(len(gaps_with_lim), 0)
        self.assertTrue(any("Scarcity" in g["gap"] or "Bottleneck" in g["gap"] for g in gaps_with_lim))


if __name__ == "__main__":
    unittest.main()
