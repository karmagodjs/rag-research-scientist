
import re
import json
import logging
from typing import List, Dict, Any, Optional
from evidence.llm_client import LLMClient

logger = logging.getLogger(__name__)


class ResearchGapAnalyzer:

    GAP_INDICATORS = [
        (r"\b(limitation|limitations|bottleneck|bottlenecks)\b", "Architectural & Scalability Bottlenecks", "Current literature highlights fundamental capacity, throughput, or architectural constraints."),
        (r"\b(robustness|out-of-distribution|noisy|adversarial|vulnerab)\b", "Robustness & Distribution Shift", "Performance degradation occurs under noisy, adversarial, or out-of-distribution environments."),
        (r"\b(hallucinat|factuality|ungrounded|misalignment|faithfulness)\b", "Factuality & Alignment Constraints", "Generative outputs remain prone to hallucinations or unsupported inferences."),
        (r"\b(scarcity|low-resource|annotat|data bottleneck|unlabeled)\b", "Data & Resource Scarcity", "Severe scarcity of annotated domain-specific corpora limits generalization in specialized domains."),
        (r"\b(generaliz|cross-domain|transfer|adaptation)\b", "Cross-Domain Transfer & Generalization Gap", "Techniques exhibit limited transferability across heterogeneous task distributions."),
        (r"\b(evaluation|standardiz|benchmark|metric|measurement)\b", "Standardized Evaluation Deficit", "Lack of comprehensive, unified evaluation protocols across diverse real-world conditions."),
        (r"\b(future work|open challenge|open problem|unresolved|remains unclear)\b", "Unresolved Research Frontiers", "Critical research questions and empirical trade-offs remain open.")
    ]

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client

    def detect_gaps(self, evidence_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        use_llm = self.llm_client is not None and self.llm_client.is_available()

        if use_llm:
            logger.info("LLM mode active for research gap detection.")
            gaps = self._detect_gaps_llm(evidence_list)
            if gaps:
                return gaps
            logger.warning("LLM gap detection produced no results. Falling back to heuristic gap analysis.")

        logger.info("Evidence-grounded heuristic mode active for gap detection.")
        return self._detect_gaps_heuristic(evidence_list)

    def _detect_gaps_llm(self, evidence_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not evidence_list:
            return []

        snippets_text = "\n".join([
            f"- [Paper: {ev['paper_id']}] {ev['snippet']}"
            for ev in evidence_list[:10]
        ])

        prompt = (
            f"Based strictly on the following scientific research snippets, identify any open research gaps or limitations explicitly highlighted in the literature:\n\n"
            f"{snippets_text}\n\n"
            f"If the literature highlights specific challenges or open gaps, respond with a JSON array of objects:\n"
            f"- \"title\": concise title of the gap\n"
            f"- \"why_it_matters\": 1-sentence explanation of why this gap is critical based on the evidence\n"
            f"- \"paper_id\": paper ID from the snippets that highlights or exemplifies this gap\n"
            f"If no research gaps or limitations are mentioned in the snippets, respond with an empty JSON array: []"
        )
        system_prompt = "You are a scientific research gap analyst. Infer real research gaps strictly from provided literature evidence."

        response = self.llm_client.generate(prompt, system_prompt)
        detected_gaps = []
        if response:
            try:
                json_str = response
                if "[" in json_str and "]" in json_str:
                    json_str = json_str[json_str.find("["):json_str.rfind("]") + 1]
                data = json.loads(json_str)

                for item in data:
                    title = item.get("title")
                    if not title:
                        continue
                    why = item.get("why_it_matters", "Requires further empirical investigation.")
                    p_id = item.get("paper_id", "")

                    matching_ev = [ev for ev in evidence_list if ev["paper_id"] == p_id]
                    if matching_ev:
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
        seen_gaps = set()

        for pattern, gap_title, why_matters in self.GAP_INDICATORS:
            matching_ev = [
                ev for ev in evidence_list
                if re.search(pattern, ev["snippet"], re.IGNORECASE)
            ]
            if matching_ev and gap_title not in seen_gaps:
                seen_gaps.add(gap_title)
                lead_ev = matching_ev[0]
                detected_gaps.append({
                    "gap": f"{gap_title}: {lead_ev['snippet'][:80]}...",
                    "evidence_for_gap": [
                        {
                            "paper_id": ev["paper_id"],
                            "snippet": ev["snippet"],
                            "source_url": ev["source_url"]
                        } for ev in matching_ev[:2]
                    ],
                    "why_it_matters": why_matters
                })

        logger.info(f"Detected {len(detected_gaps)} evidence-backed literature gaps.")
        return detected_gaps

    def propose_next_research(
        self,
        gaps: List[Dict[str, Any]],
        evidence_graph: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        if not gaps:
            logger.info("No gaps identified; no speculative research proposals generated.")
            return []

        proposals = []
        for idx, gap in enumerate(gaps[:4]):
            gap_title = gap["gap"]
            ev_refs = [e["source_url"] for e in gap.get("evidence_for_gap", []) if e.get("source_url")]

            proposals.append({
                "research_direction": f"Investigation Framework for {gap_title.split(':')[0]}",
                "motivation": f"Directly addresses {gap['why_it_matters']} identified in retrieved literature.",
                "evidence": ev_refs,
                "novelty": "Integrates empirical verification and systematic benchmark analysis.",
                "difficulty": "Medium-High",
                "expected_impact": "Substantially advances reliability and clarity on unaddressed domain challenges."
            })

        logger.info(f"Formulated {len(proposals)} research proposals.")
        return proposals
