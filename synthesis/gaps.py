"""
Research Gap Analyzer and Next-Step Proposal module.
Infere open research gaps dynamically from literature patterns and constructs actionable research proposals.
Supports LLM-backed gap inference with generic non-domain-specific heuristic fallback.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from evidence.llm_client import LLMClient

logger = logging.getLogger(__name__)


class ResearchGapAnalyzer:
    """Detects literature gaps dynamically and formulates evidence-backed research proposals."""

    GENERIC_GAP_PATTERNS = [
        ("evaluation", "Evaluation Deficit", "Insufficient standardized benchmarks across diverse real-world conditions."),
        ("robustness", "Robustness Deficit", "Sensitivity or performance degradation when handling noisy or out-of-distribution inputs."),
        ("hallucination", "Fidelity & Alignment Gap", "System output misalignment or ungrounded generative artifacts under complex queries."),
        ("data", "Resource & Data Bottleneck", "Scarcity of high-quality, diverse paired training datasets for specialized sub-domains."),
        ("generalization", "Generalization Deficit", "Limited cross-domain transfer performance across varied operating regimes.")
    ]

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client

    def detect_gaps(self, evidence_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Infer open research gaps dynamically from retrieved evidence snippets."""
        use_llm = self.llm_client is not None and self.llm_client.is_available()

        if use_llm:
            logger.info("LLM mode active for research gap detection.")
            gaps = self._detect_gaps_llm(evidence_list)
            if gaps:
                return gaps
            logger.warning("LLM gap detection produced no results. Falling back to generic heuristic gap analysis.")

        logger.info("Generic heuristic mode active for gap detection (no LLM API key configured).")
        return self._detect_gaps_heuristic(evidence_list)

    def _detect_gaps_llm(self, evidence_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not evidence_list:
            return []

        snippets_text = "\n".join([
            f"- [Paper: {ev['paper_id']}] {ev['snippet']}"
            for ev in evidence_list[:10]
        ])

        prompt = (
            f"Based on the following scientific research snippets, infer 3 open research gaps or unaddressed challenges in this domain:\n\n"
            f"{snippets_text}\n\n"
            f"Respond ONLY with a JSON array of objects, where each object has:\n"
            f"- \"title\": concise title of the gap (e.g. \"Cross-Domain Evaluation Deficit\")\n"
            f"- \"why_it_matters\": 1-sentence explanation of why this gap is critical\n"
            f"- \"paper_id\": paper ID from the snippets that highlights or exemplifies this gap\n"
        )
        system_prompt = "You are a scientific research gap analyst. Infer real research gaps strictly from provided literature evidence."

        response = self.llm_client.generate(prompt, system_prompt)
        detected_gaps = []
        if response:
            try:
                json_str = response
                if "[" in json_str and "]" in json_str:
                    json_str = json_str[json_str.find("["):json_str.rfind("]")+1]
                data = json.loads(json_str)

                for item in data:
                    title = item.get("title", "Unresolved Research Gap")
                    why = item.get("why_it_matters", "Requires further empirical investigation.")
                    p_id = item.get("paper_id", "")

                    matching_ev = [ev for ev in evidence_list if ev["paper_id"] == p_id]
                    if not matching_ev:
                        matching_ev = evidence_list[:1]

                    detected_gaps.append({
                        "gap": f"{title}: {matching_ev[0]['snippet'][:60]}...",
                        "evidence_for_gap": [
                            {
                                "paper_id": ev["paper_id"],
                                "snippet": ev["snippet"],
                                "source_url": ev["source_url"]
                            } for ev in matching_ev[:2]
                        ],
                        "why_it_matters": why
                    })
            except Exception as e:
                logger.warning(f"Failed to parse LLM research gap response: {e}")

        return detected_gaps

    def _detect_gaps_heuristic(self, evidence_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        detected_gaps = []

        for kw, gap_title, why_matters in self.GENERIC_GAP_PATTERNS:
            matching_ev = [ev for ev in evidence_list if kw in ev["snippet"].lower()]
            if matching_ev:
                detected_gaps.append({
                    "gap": f"{gap_title}: {matching_ev[0]['snippet'][:60]}...",
                    "evidence_for_gap": [
                        {
                            "paper_id": ev["paper_id"],
                            "snippet": ev["snippet"],
                            "source_url": ev["source_url"]
                        } for ev in matching_ev[:2]
                    ],
                    "why_it_matters": why_matters
                })

        # Generic fallback if specific keywords are absent in small evidence pools
        if not detected_gaps and evidence_list:
            detected_gaps.append({
                "gap": "Cross-Domain Generalization Deficit in Complex Regimes",
                "evidence_for_gap": [
                    {
                        "paper_id": evidence_list[0]["paper_id"],
                        "snippet": evidence_list[0]["snippet"],
                        "source_url": evidence_list[0]["source_url"]
                    }
                ],
                "why_it_matters": "Current literature lacks comprehensive empirical verification across diverse operating environments."
            })

        logger.info(f"Detected {len(detected_gaps)} literature gaps.")
        return detected_gaps

    def propose_next_research(
        self,
        gaps: List[Dict[str, Any]],
        evidence_graph: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Construct actionable research directions anchored in the evidence graph."""
        proposals = []

        for idx, gap in enumerate(gaps[:4]):
            gap_title = gap["gap"]
            ev_refs = [e["source_url"] for e in gap["evidence_for_gap"]]

            proposals.append({
                "research_direction": f"Graph-Grounded Framework for {gap_title.split(':')[0]}",
                "motivation": f"Directly addresses {gap['why_it_matters']} identified in retrieved literature.",
                "evidence": ev_refs,
                "novelty": "Combines dynamic retrieval-augmented verification with structural evidence graph constraints.",
                "difficulty": "Medium-High",
                "expected_impact": "Substantially improves performance stability and reduces error rates on underrepresented domain tasks."
            })

        logger.info(f"Formulated {len(proposals)} research proposals.")
        return proposals
