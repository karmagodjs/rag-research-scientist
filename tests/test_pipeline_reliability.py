# -*- coding: utf-8 -*-
"""
Comprehensive Pipeline Reliability & Feature Test Suite
Covers:
- Canonical papers exclusion from production retrieval
- Semantic retrieval integration
- ArXiv instance URL usage and HTTP 429 resilience
- Exact title retrieval and score boosting
- Contradiction 4-state analysis
- Evidence-backed research gap validation
- Temporal query extraction & preservation
- Date-aware ranking prioritization
- Unknown web publication year handling (never defaults to 2025)
- Real relevance and evidence_count metrics in report citations
- Aspect-aware evidence extraction
"""

import unittest
from unittest.mock import MagicMock, patch
from retrieval.base import Document
from retrieval.arxiv import ArxivRetriever
from retrieval.web import WebRetriever
from retrieval.semantic import SemanticRetriever
from retrieval.dedup import DocumentDeduplicator
from retrieval.decomposer import QueryDecomposer
from retrieval.query_utils import (
    extract_temporal_constraints,
    calculate_temporal_score,
    parse_publication_year,
    detect_exact_paper_query
)
from ranking.reranker import Reranker
from evidence.extractor import EvidenceExtractor
from evidence.claims import ClaimGenerator
from evidence.contradiction import ContradictionDetector
from synthesis.gaps import ResearchGapAnalyzer
from synthesis.report import ReportSynthesizer
from agent import ResearchAgent, AgentConfig


class TestPipelineReliability(unittest.TestCase):

    def test_canonical_papers_not_injected_in_unrelated_queries(self):
        agent = ResearchAgent(config=AgentConfig(timeout_seconds=2))
        
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

    def test_temporal_query_extraction_and_decomposition(self):
        # Test temporal extraction
        t1 = extract_temporal_constraints("OCR for low-resource Indic languages since 2024")
        self.assertTrue(t1["has_temporal_constraint"])
        self.assertEqual(t1["min_year"], 2024)

        t2 = extract_temporal_constraints("Evolution of vision-language models after 2023")
        self.assertTrue(t2["has_temporal_constraint"])
        self.assertEqual(t2["min_year"], 2024)

        t3 = extract_temporal_constraints("multimodal models from 2023 to 2025")
        self.assertTrue(t3["has_temporal_constraint"])
        self.assertEqual(t3["min_year"], 2023)
        self.assertEqual(t3["max_year"], 2025)

        # Test complex multi-aspect query decomposition
        complex_query = "How has OCR for low-resource Indic languages evolved since 2024, what methods currently perform best, what limitations remain, and what research directions are still unexplored?"
        decomposer = QueryDecomposer()
        subqueries = decomposer.decompose(complex_query)

        # Original query must be preserved as subquery 1
        self.assertEqual(subqueries[0], complex_query)
        self.assertGreaterEqual(len(subqueries), 3)

        # Subqueries should capture aspect dimensions
        joined_sqs = " ".join(subqueries).lower()
        self.assertTrue("since 2024" in joined_sqs or "evolution" in joined_sqs or "2024" in joined_sqs)
        self.assertTrue("methods" in joined_sqs or "best" in joined_sqs or "state of the art" in joined_sqs)
        self.assertTrue("limitations" in joined_sqs or "challenges" in joined_sqs)

    def test_date_aware_ranking_prioritizes_recent_papers(self):
        reranker = Reranker()
        
        # Two papers with identical titles/abstracts except publication year
        doc_old = Document(
            id="p_old",
            title="Printed OCR for Low-Resource Indic Languages",
            authors=["R. Kumar"],
            abstract="We present an OCR system for low-resource Indic scripts achieving good character accuracy.",
            url="http://example.com/2019",
            published="2019",
            source="arXiv",
            content="Printed OCR for Low-Resource Indic Languages"
        )
        doc_recent = Document(
            id="p_recent",
            title="Printed OCR for Low-Resource Indic Languages",
            authors=["S. Sharma"],
            abstract="We present an OCR system for low-resource Indic scripts achieving good character accuracy.",
            url="http://example.com/2025",
            published="2025",
            source="arXiv",
            content="Printed OCR for Low-Resource Indic Languages"
        )

        # Query WITH temporal constraint: recent paper must rank #1
        temporal_query = "OCR for low-resource Indic languages since 2024"
        ranked = reranker.rerank(temporal_query, [doc_old, doc_recent])
        self.assertEqual(ranked[0].id, "p_recent")
        self.assertEqual(ranked[1].id, "p_old")
        self.assertGreater(ranked[0].metadata["final_score"], ranked[1].metadata["final_score"])

        # Query WITHOUT temporal constraint: does not artificially distort ranking
        unconstrained_query = "OCR for low-resource Indic languages"
        ranked_unconstrained = reranker.rerank(unconstrained_query, [doc_old, doc_recent])
        self.assertEqual(len(ranked_unconstrained), 2)

    def test_web_retriever_unknown_year_not_hardcoded_2025(self):
        web = WebRetriever()
        
        # Test OpenAlex result with missing publication_year
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "results": [
                    {
                        "id": "https://openalex.org/W123",
                        "title": "Ancient Script Decipherment",
                        "publication_year": None,
                        "doi": None,
                        "authorships": [{"author": {"display_name": "Dr. Historian"}}],
                        "abstract_inverted_index": {"Study": [0], "of": [1], "scripts": [2]}
                    }
                ]
            }
            mock_get.return_value = mock_resp

            docs = web._search_academic_web("Ancient Script Decipherment", top_k=1)
            self.assertEqual(len(docs), 1)
            self.assertEqual(docs[0].published, "unknown")
            self.assertNotEqual(docs[0].published, "2025")

    def test_report_citation_has_real_relevance_and_evidence_count(self):
        synthesizer = ReportSynthesizer()
        doc = Document(
            id="doc1",
            title="Transformer Attention Models",
            authors=["A. Author"],
            abstract="Self-attention mechanism.",
            url="http://example.com/1",
            published="2024",
            source="arXiv",
            metadata={"final_score": 0.88}
        )
        evidence = [
            {"paper_id": "doc1", "snippet": "Self-attention achieves high throughput.", "source_url": "http://example.com/1", "relevance_score": 0.92},
            {"paper_id": "doc1", "snippet": "Multi-head attention allows joint attending.", "source_url": "http://example.com/1", "relevance_score": 0.85},
            {"paper_id": "other_doc", "snippet": "Another snippet.", "source_url": "http://example.com/2", "relevance_score": 0.7}
        ]

        report = synthesizer.build_full_report(
            query="Transformer Attention Models",
            documents=[doc],
            claims=[],
            contradictions=[],
            evidence_graph={},
            timeline={},
            gaps=[],
            next_research=[],
            stats={},
            evidence_snippets=evidence
        )

        citation = report["citation_list"][0]
        self.assertEqual(citation["id"], "doc1")
        self.assertEqual(citation["relevance"], 0.88)
        self.assertEqual(citation["evidence_count"], 2)
        self.assertEqual(citation["published"], "2024")

    def test_aspect_aware_evidence_extraction(self):
        extractor = EvidenceExtractor()
        doc = Document(
            id="doc_vlm",
            title="Vision Language Models for Low-Resource OCR",
            authors=["Researcher"],
            abstract="We propose an end-to-end VLM for Indic OCR. A major bottleneck is the severe degradation on degraded historical documents. The model achieves 94% accuracy on printed text.",
            url="http://example.com/vlm",
            published="2024",
            source="arXiv",
            metadata={"final_score": 0.9}
        )

        evidence = extractor.extract_evidence([doc], "How has OCR evolved, what methods perform best, and what limitations remain?")
        self.assertGreaterEqual(len(evidence), 2)
        
        # Check aspect tagging
        aspects = [ev.get("aspect") for ev in evidence]
        self.assertTrue("limitations" in aspects or "methods" in aspects or "findings" in aspects)
        self.assertTrue(all(ev["source_type"] == "abstract" for ev in evidence))

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
        
        # Snippets with standard empirical findings (not limitation / bottleneck)
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

        # Snippets with explicit substantive limitations
        limitation_evidence = [
            {
                "paper_id": "p2",
                "paper_title": "Vision Language Models",
                "snippet": "A major bottleneck is the severe scarcity of annotated parallel data in low-resource Indic languages.",
                "source_url": "http://example.com/2",
                "relevance_score": 0.95
            }
        ]
        gaps_with_lim = analyzer.detect_gaps(limitation_evidence)
        self.assertGreater(len(gaps_with_lim), 0)
        self.assertTrue(any("Scarcity" in g["gap"] or "Bottleneck" in g["gap"] for g in gaps_with_lim))


if __name__ == "__main__":
    unittest.main()
