
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
        expected_keywords: List[str] = None,
        expected_title: str = None,
        is_exact_title: bool = False
    ) -> Dict[str, float]:
        total_unique = len(retrieved_docs)

        duplicate_rate = 0.0
        if raw_retrieved_count > 0:
            duplicate_rate = round(max(0.0, (raw_retrieved_count - total_unique) / raw_retrieved_count), 2)

        def get_doc_text(doc):
            if hasattr(doc, "title"):
                return f"{doc.title} {getattr(doc, 'abstract', '')}".lower()
            return f"{doc.get('title', '')} {doc.get('abstract', '')}".lower()

        def is_doc_relevant(doc):
            if not doc:
                return False
            t = get_doc_text(doc)
            if is_exact_title and expected_title:
                norm_exp = "".join(c for c in expected_title.lower() if c.isalnum() or c.isspace()).strip()
                norm_title = "".join(c for c in (doc.title if hasattr(doc, "title") else doc.get("title", "")).lower() if c.isalnum() or c.isspace()).strip()
                if norm_exp in norm_title or norm_title in norm_exp:
                    return True
            if expected_keywords:
                return any(kw.lower() in t for kw in expected_keywords)
            return True

        # Relevant document retrieval precision
        precision = 0.0
        if total_unique > 0:
            relevant_count = sum(1 for doc in retrieved_docs if is_doc_relevant(doc))
            precision = round(relevant_count / total_unique, 2)

        # Top-1 and Top-3 retrieval metrics
        top_1_retrieval = 1.0 if (total_unique > 0 and is_doc_relevant(retrieved_docs[0])) else 0.0
        top_3_retrieval = 1.0 if (total_unique > 0 and any(is_doc_relevant(d) for d in retrieved_docs[:3])) else 0.0

        # Evidence availability and grounding
        all_ev = [ev for c in claims for ev in c.get("evidence", [])]
        evidence_availability = 1.0 if len(all_ev) > 0 else 0.0

        valid_urls = sum(1 for ev in all_ev if ev.get("source_url") and str(ev["source_url"]).startswith("http"))
        evidence_grounding = round(valid_urls / len(all_ev), 2) if all_ev else 0.0

        claims_with_citations = sum(1 for c in claims if len(c.get("evidence", [])) > 0)
        citation_coverage = round(claims_with_citations / len(claims), 2) if claims else 0.0

        detected_contradictions = sum(1 for c in contradictions if str(c.get("status", "")).lower() in {"contradicted", "mixed"})
        contradiction_detection_rate = round(detected_contradictions / len(contradictions), 2) if contradictions else 0.0

        metrics = {
            "top_1_retrieval": top_1_retrieval,
            "top_3_retrieval": top_3_retrieval,
            "retrieval_precision": precision,
            "evidence_availability": evidence_availability,
            "evidence_grounding": evidence_grounding,
            "citation_coverage": citation_coverage,
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
            expected_title = sample.get("expected_title")
            is_exact = sample.get("is_exact_title", False)

            report = agent_instance.run(query=query)
            metrics = self.evaluate_run(
                retrieved_docs=report.get("citation_list", []),
                raw_retrieved_count=report.get("retrieval_statistics", {}).get("raw_documents", 0),
                claims=report.get("claims", []),
                contradictions=report.get("contradiction_analysis", []),
                expected_keywords=expected_kws,
                expected_title=expected_title,
                is_exact_title=is_exact
            )
            results.append({
                "id": sample.get("id"),
                "query": query,
                "metrics": metrics,
                "top_retrieved_paper": report.get("citation_list", [{}])[0].get("title", "None") if report.get("citation_list") else "None",
                "num_claims": len(report.get("claims", []))
            })

        avg_top1 = sum(r["metrics"]["top_1_retrieval"] for r in results) / len(results) if results else 0.0
        avg_top3 = sum(r["metrics"]["top_3_retrieval"] for r in results) / len(results) if results else 0.0
        avg_precision = sum(r["metrics"]["retrieval_precision"] for r in results) / len(results) if results else 0.0
        avg_grounding = sum(r["metrics"]["evidence_grounding"] for r in results) / len(results) if results else 0.0
        avg_avail = sum(r["metrics"]["evidence_availability"] for r in results) / len(results) if results else 0.0

        return {
            "num_queries_evaluated": len(results),
            "mean_top_1_retrieval": round(avg_top1, 2),
            "mean_top_3_retrieval": round(avg_top3, 2),
            "mean_retrieval_precision": round(avg_precision, 2),
            "mean_evidence_availability": round(avg_avail, 2),
            "mean_evidence_grounding": round(avg_grounding, 2),
            "individual_results": results
        }
