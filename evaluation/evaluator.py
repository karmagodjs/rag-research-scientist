
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class Evaluator:

    def evaluate_run(
        self,
        retrieved_docs: List[Any],
        raw_retrieved_count: int,
        claims: List[Dict[str, Any]],
        contradictions: List[Dict[str, Any]],
        expected_keywords: List[str] = None
    ) -> Dict[str, float]:
        total_unique = len(retrieved_docs)

        duplicate_rate = 0.0
        if raw_retrieved_count > 0:
            duplicate_rate = round(max(0.0, (raw_retrieved_count - total_unique) / raw_retrieved_count), 2)


        precision = 1.0
        if expected_keywords and total_unique > 0:
            relevant_count = 0
            for doc in retrieved_docs:
                text = f"{doc.title} {doc.abstract}".lower() if hasattr(doc, "title") else f"{doc['title']} {doc['abstract']}".lower()
                if any(kw.lower() in text for kw in expected_keywords):
                    relevant_count += 1
            precision = round(relevant_count / total_unique, 2)


        claims_with_citations = sum(1 for c in claims if len(c.get("evidence", [])) > 0)
        citation_coverage = round(claims_with_citations / len(claims), 2) if claims else 0.0


        all_ev = [ev for c in claims for ev in c.get("evidence", [])]
        grounded_ev = sum(1 for ev in all_ev if ev.get("source_url"))
        evidence_grounding = round(grounded_ev / len(all_ev), 2) if all_ev else 0.0


        detected_contradictions = sum(1 for c in contradictions if c.get("status") in {"contradicted", "mixed"})
        contradiction_detection_rate = round(detected_contradictions / len(contradictions), 2) if contradictions else 0.0

        metrics = {
            "retrieval_precision": precision,
            "citation_coverage": citation_coverage,
            "evidence_grounding": evidence_grounding,
            "duplicate_rate": duplicate_rate,
            "contradiction_detection_rate": contradiction_detection_rate,
        }
        logger.info(f"Evaluation Metrics Computed: {metrics}")
        return metrics

    def run_benchmark(self, benchmark_file_path: str, agent_instance) -> Dict[str, Any]:
        with open(benchmark_file_path, "r", encoding="utf-8") as f:
            benchmark_data = json.load(f)

        results = []
        for sample in benchmark_data.get("questions", []):
            query = sample["query"]
            expected_kws = sample.get("expected_keywords", [])
            report = agent_instance.run(query=query)
            metrics = self.evaluate_run(
                retrieved_docs=report["citation_list"],
                raw_retrieved_count=report["retrieval_statistics"]["raw_documents"],
                claims=report["claims"],
                contradictions=report["contradiction_analysis"],
                expected_keywords=expected_kws
            )
            results.append({"query": query, "metrics": metrics})

        avg_precision = sum(r["metrics"]["retrieval_precision"] for r in results) / len(results) if results else 0.0
        avg_grounding = sum(r["metrics"]["evidence_grounding"] for r in results) / len(results) if results else 0.0

        return {
            "num_queries_evaluated": len(results),
            "mean_retrieval_precision": round(avg_precision, 2),
            "mean_evidence_grounding": round(avg_grounding, 2),
            "individual_results": results
        }
