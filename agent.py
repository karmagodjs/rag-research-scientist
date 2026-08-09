#!/usr/bin/env python3
"""
RAG Research Scientist Agent — Core Orchestration Module
Executes end-to-end evidence-grounded research agent pipeline with dynamic self-improvement loops.
"""

import sys
import os
import json
import argparse
import logging
from typing import List, Dict, Any

# Internal imports
from config import AgentConfig
from retrieval.base import Document
from retrieval.arxiv import ArxivRetriever
from retrieval.web import WebRetriever
from retrieval.semantic import SemanticRetriever
from retrieval.dedup import DocumentDeduplicator
from retrieval.decomposer import QueryDecomposer
from ranking.reranker import Reranker
from evidence.extractor import EvidenceExtractor
from evidence.llm_client import LLMClient
from evidence.claims import ClaimGenerator
from evidence.contradiction import ContradictionDetector
from evidence.graph import EvidenceGraph
from synthesis.timeline import TimelineGenerator
from synthesis.gaps import ResearchGapAnalyzer
from synthesis.report import ReportSynthesizer
from evaluation.evaluator import Evaluator


class ResearchAgent:
    """Production-grade RAG Research Scientist Agent orchestrator."""

    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        
        # Setup logging
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper(), logging.INFO),
            format=log_format
        )
        self.logger = logging.getLogger("ResearchAgent")

        # Initialize LLM Client
        self.llm_client = LLMClient(
            anthropic_api_key=self.config.anthropic_api_key,
            openai_api_key=self.config.openai_api_key,
            gemini_api_key=self.config.gemini_api_key,
            timeout=self.config.timeout_seconds
        )

        # Initialize sub-components
        self.decomposer = QueryDecomposer()
        self.arxiv_retriever = ArxivRetriever(api_url=self.config.arxiv_api_url, timeout=self.config.timeout_seconds)
        self.web_retriever = WebRetriever(tavily_api_key=self.config.tavily_api_key, timeout=self.config.timeout_seconds)
        self.semantic_retriever = SemanticRetriever()
        self.deduplicator = DocumentDeduplicator()
        self.reranker = Reranker()
        self.extractor = EvidenceExtractor()
        self.claim_generator = ClaimGenerator(llm_client=self.llm_client)
        self.contradiction_detector = ContradictionDetector(llm_client=self.llm_client)
        self.graph_builder = EvidenceGraph()
        self.timeline_generator = TimelineGenerator()
        self.gap_analyzer = ResearchGapAnalyzer(llm_client=self.llm_client)
        self.synthesizer = ReportSynthesizer()
        self.evaluator = Evaluator()


    def run(self, query: str) -> Dict[str, Any]:
        """Execute self-improving research pipeline over max_iterations."""
        self.logger.info(f"Starting Research Pipeline for query: '{query}'")
        
        all_documents: List[Document] = []
        raw_retrieved_count = 0
        iteration = 0
        current_queries = [query]

        # 1. Self-Improvement Retrieval Loop
        while iteration < self.config.max_iterations:
            iteration += 1
            self.logger.info(f"--- Self-Improvement Loop Iteration {iteration}/{self.config.max_iterations} ---")

            # Query Decomposition
            subqueries = []
            for q in current_queries:
                subqueries.extend(self.decomposer.decompose(q))
            subqueries = list(dict.fromkeys(subqueries))[:4]  # unique top subqueries

            iteration_docs: List[Document] = []

            # Retrieve across subqueries and multi-sources with rate-limiting respect
            import time
            for sq in subqueries:
                arxiv_docs = self.arxiv_retriever.search(sq, top_k=3)
                time.sleep(0.3)  # Respect arXiv API rate limit
                web_docs = self.web_retriever.search(sq, top_k=2)
                iteration_docs.extend(arxiv_docs)
                iteration_docs.extend(web_docs)

            raw_retrieved_count += len(iteration_docs)

            # Deduplication
            combined_pool = self.deduplicator.deduplicate(all_documents + iteration_docs)
            all_documents = combined_pool

            # Rerank document pool
            ranked_docs = self.reranker.rerank(query, all_documents, top_k=self.config.max_papers)
            all_documents = ranked_docs

            # Check if evidence gap requires another iteration
            if len(all_documents) >= 5 or iteration >= self.config.max_iterations:
                self.logger.info("Sufficient document pool retrieved or max iterations reached.")
                break
            else:
                # Formulate refined queries for next iteration
                self.logger.info("Document pool sparse; reformulating search queries for self-improvement step.")
                current_queries = [f"{query} survey benchmark", f"{query} systematic evaluation"]

        # If zero documents retrieved from all sources
        if not all_documents:
            self.logger.warning("RETRIEVAL_FAILURE: Zero documents were retrieved from any source.")
            return {
                "research_question": query,
                "executive_summary": f"RETRIEVAL_FAILURE: No documents found across arXiv or web sources for query '{query}'. Per system rules, no fake data was generated.",
                "status": "RETRIEVAL_FAILURE",
                "retrieval_statistics": {
                    "total_documents": 0,
                    "raw_documents": raw_retrieved_count,
                    "num_subqueries": len(subqueries),
                    "iterations": iteration,
                },
                "claims": [],
                "contradiction_analysis": [],
                "research_timeline": {},
                "open_research_gaps": [],
                "what_to_research_next": [],
                "evidence_graph": {"nodes": [], "edges": []},
                "citation_list": []
            }

        # 2. Semantic Index Update
        self.semantic_retriever.set_corpus(all_documents)

        # 3. Evidence Extraction
        evidence_snippets = self.extractor.extract_evidence(all_documents, query)

        # 4. Claim Generation & Confidence Calculation
        claims = self.claim_generator.generate_claims(evidence_snippets)

        # 5. Contradiction Analysis
        contradictions = [
            self.contradiction_detector.analyze_claim(c, evidence_snippets)
            for c in claims
        ]

        # 6. Evidence Graph Construction
        evidence_graph = self.graph_builder.build_graph(query, claims, contradictions, all_documents)

        # 7. Timeline Generation
        timeline = self.timeline_generator.generate_timeline(all_documents)

        # 8. Research Gap & Next Step Analysis
        gaps = self.gap_analyzer.detect_gaps(evidence_snippets)
        next_research = self.gap_analyzer.propose_next_research(gaps, evidence_graph)

        # 9. Retrieval & System Statistics
        stats = {
            "total_documents": len(all_documents),
            "raw_documents": raw_retrieved_count,
            "num_subqueries": len(subqueries),
            "iterations": iteration,
        }

        # 10. Report Synthesis
        full_report = self.synthesizer.build_full_report(
            query=query,
            documents=all_documents,
            claims=claims,
            contradictions=contradictions,
            evidence_graph=evidence_graph,
            timeline=timeline,
            gaps=gaps,
            next_research=next_research,
            stats=stats
        )

        return full_report


def main():
    parser = argparse.ArgumentParser(description="RAG Research Scientist Agent CLI")
    parser.add_argument("--query", type=str, required=True, help="User research question")
    parser.add_argument("--max-papers", type=int, default=15, help="Maximum papers in reranked pool")
    parser.add_argument("--max-iterations", type=int, default=2, help="Self-improvement search loop iterations")
    parser.add_argument("--output", type=str, default="report.json", help="Output JSON path")
    parser.add_argument("--markdown", type=str, default="report.md", help="Output Markdown path")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--evaluate", action="store_true", help="Run benchmark evaluation suite")
    args = parser.parse_args()

    config = AgentConfig(
        max_papers=args.max_papers,
        max_iterations=args.max_iterations,
        output_path=args.output,
        markdown_output_path=args.markdown,
        verbose=args.verbose,
        log_level="DEBUG" if args.verbose else "INFO"
    )

    agent = ResearchAgent(config=config)

    if args.evaluate:
        print("[*] Running Benchmark Evaluation Framework...")
        bench_path = os.path.join(os.path.dirname(__file__), "data", "benchmark.json")
        if os.path.exists(bench_path):
            res = agent.evaluator.run_benchmark(bench_path, agent)
            print(json.dumps(res, indent=2))
        else:
            print(f"[!] Benchmark file not found at {bench_path}")
        return

    # Execute research agent run
    print(f"[*] Executing Research Scientist Agent for: '{args.query}'...")
    report = agent.run(args.query)

    # Save JSON report
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"[OK] Saved JSON report to {args.output}")

    # Save Markdown report
    if args.markdown:
        md_text = agent.synthesizer.render_markdown(report)
        with open(args.markdown, "w", encoding="utf-8") as f:
            f.write(md_text)
        print(f"[OK] Saved Markdown report to {args.markdown}")

    # Print summary to stdout
    print(f"\nCompleted analysis. Retrieved {report.get('retrieval_statistics', {}).get('total_documents', 0)} documents.")
    print(f"Generated {len(report.get('claims', []))} claims and {len(report.get('what_to_research_next', []))} future research proposals.\n")


if __name__ == "__main__":
    main()
