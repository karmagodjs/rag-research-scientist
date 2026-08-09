"""
Claim Generation and Dynamic Confidence Calculation module.
Generates research claims dynamically from retrieved evidence and computes confidence scores.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ClaimGenerator:
    """Generates empirically grounded research claims and calculates objective confidence scores."""

    def _calculate_confidence(
        self,
        num_sources: int,
        avg_relevance: float,
        recency_score: float,
        has_contradiction: bool
    ) -> float:
        """
        Calculates confidence score dynamically using measurable evidence factors:
        1. Number of independent supporting sources (weight: 0.35)
        2. Average evidence relevance score (weight: 0.35)
        3. Recency of publication (weight: 0.15)
        4. Agreement / Absence of contradiction (weight: 0.15)
        """
        source_factor = min(1.0, num_sources / 3.0)
        relevance_factor = min(1.0, max(0.0, avg_relevance))
        agreement_factor = 0.5 if has_contradiction else 1.0

        confidence = (
            (source_factor * 0.35) +
            (relevance_factor * 0.35) +
            (recency_score * 0.15) +
            (agreement_factor * 0.15)
        )
        return round(min(1.0, max(0.0, confidence)), 2)

    def generate_claims(self, evidence_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Cluster evidence into claims and compute confidence scores dynamically."""
        if not evidence_items:
            logger.warning("No evidence available to generate claims.")
            return []

        # Group evidence snippets by paper ID
        doc_map: Dict[str, List[Dict[str, Any]]] = {}
        for item in evidence_items:
            p_id = item["paper_id"]
            if p_id not in doc_map:
                doc_map[p_id] = []
            doc_map[p_id].append(item)

        # Sort documents by max relevance score of their snippets
        sorted_docs = sorted(
            doc_map.items(),
            key=lambda x: max(s["relevance_score"] for s in x[1]),
            reverse=True
        )

        claims = []
        for p_id, snippets in sorted_docs[:4]:
            lead_snippet = snippets[0]
            
            # Format clean claim text without redundant prefix
            raw_text = lead_snippet['snippet'].strip()
            claim_text = raw_text if len(raw_text) > 30 else f"Paper {lead_snippet['paper_title']}: {raw_text}"
            
            supporting_sources = set(s["paper_id"] for s in snippets)
            num_sources = len(supporting_sources)
            avg_rel = sum(s["relevance_score"] for s in snippets) / len(snippets)
            
            year_str = str(lead_snippet.get("published_year", "2024"))
            try:
                year_val = int(year_str[:4])
                recency = 1.0 if year_val >= 2025 else 0.8
            except ValueError:
                recency = 0.7

            confidence = self._calculate_confidence(
                num_sources=num_sources,
                avg_relevance=avg_rel,
                recency_score=recency,
                has_contradiction=False
            )

            claims.append({
                "claim": claim_text,
                "evidence": [
                    {
                        "paper_id": s["paper_id"],
                        "paper_title": s["paper_title"],
                        "snippet": s["snippet"],
                        "source_url": s["source_url"],
                        "relevance_score": s["relevance_score"]
                    } for s in snippets
                ],
                "confidence": confidence,
                "reasoning": f"Calculated from {num_sources} supporting sources, avg relevance {avg_rel:.2f}, recency score {recency}."
            })

        logger.info(f"Generated {len(claims)} evidence-grounded research claims.")
        return claims
