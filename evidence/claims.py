
import logging
from typing import List, Dict, Any, Optional
from evidence.llm_client import LLMClient

logger = logging.getLogger(__name__)


class ClaimGenerator:

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client

    def _calculate_confidence(
        self,
        num_sources: int,
        avg_relevance: float,
        recency_score: float,
        has_contradiction: bool
    ) -> float:
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
        if not evidence_items:
            logger.warning("No evidence available to generate claims.")
            return []

        use_llm = self.llm_client is not None and self.llm_client.is_available()
        if use_llm:
            logger.info("LLM mode active for claim synthesis.")
        else:
            logger.info("Heuristic mode active for claim synthesis (no LLM API key configured).")


        doc_map: Dict[str, List[Dict[str, Any]]] = {}
        for item in evidence_items:
            p_id = item["paper_id"]
            if p_id not in doc_map:
                doc_map[p_id] = []
            doc_map[p_id].append(item)


        sorted_docs = sorted(
            doc_map.items(),
            key=lambda x: max(s["relevance_score"] for s in x[1]),
            reverse=True
        )

        claims = []
        for p_id, snippets in sorted_docs[:4]:
            lead_snippet = snippets[0]
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

            claim_text = ""
            reasoning = ""

            if use_llm:
                paper_title = lead_snippet.get("paper_title", p_id)
                snippets_text = "\n".join([f"- {s['snippet']}" for s in snippets])
                prompt = (
                    f"Synthesize a clear, 1-sentence scientific claim from the following evidence snippets for paper '{paper_title}':\n"
                    f"{snippets_text}\n\n"
                    f"Also provide a 1-sentence qualitative reasoning explaining the confidence level or caveats of this claim.\n"
                    f"Output format:\nClaim: <1 sentence claim>\nReasoning: <1 sentence reasoning>"
                )
                system_prompt = "You are a scientific research synthesis assistant. Output concise, accurate scientific claims backed strictly by provided snippets."
                response = self.llm_client.generate(prompt, system_prompt)

                if response and "Claim:" in response:
                    lines = response.split("\n")
                    claim_line = next((l for l in lines if l.startswith("Claim:")), "")
                    reason_line = next((l for l in lines if l.startswith("Reasoning:")), "")

                    claim_text = claim_line.replace("Claim:", "").strip()
                    qualitative_reasoning = reason_line.replace("Reasoning:", "").strip()

                    if claim_text:
                        reasoning = (
                            f"{qualitative_reasoning} "
                            f"(Quantitative score: {confidence} derived from {num_sources} source(s), avg relevance {avg_rel:.2f}, recency {recency})."
                        )


            if not claim_text:
                raw_text = lead_snippet['snippet'].strip()
                claim_text = raw_text if len(raw_text) > 30 else f"Paper {lead_snippet['paper_title']}: {raw_text}"
                reasoning = f"Calculated from {num_sources} supporting source(s), avg relevance {avg_rel:.2f}, recency score {recency}."

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
                "reasoning": reasoning
            })

        logger.info(f"Generated {len(claims)} evidence-grounded research claims.")
        return claims
