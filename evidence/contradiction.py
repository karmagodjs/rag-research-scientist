"""
Contradiction Detection and Analysis module.
Analyzes evidence for agreement, disagreement, and inconclusive status across papers.
Supports LLM-backed agreement judgment with keyword heuristic fallback.
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional
from evidence.llm_client import LLMClient

logger = logging.getLogger(__name__)


class ContradictionDetector:
    """Detects supporting, contradicting, and inconclusive evidence for generated claims."""

    CONTRADICTION_KEYWORDS = {
        "however", "fails", "failed", "struggles", "inferior", "contrast", 
        "contradicts", "limitation", "inaccurate", "hallucination", "drop", "degrades"
    }

    SUPPORTING_KEYWORDS = {
        "outperforms", "improves", "surpasses", "effective", "superior", 
        "state-of-the-art", "reduces", "enhances", "robust", "achieves"
    }

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client

    def analyze_claim(self, claim: Dict[str, Any], all_evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze evidence items against a claim to detect agreement or disagreement."""
        use_llm = self.llm_client is not None and self.llm_client.is_available()
        
        if use_llm:
            logger.info(f"LLM mode active for contradiction analysis of claim: '{claim.get('claim', '')[:40]}...'")
            return self._analyze_claim_llm(claim, all_evidence)
        else:
            logger.info("Heuristic keyword mode active for contradiction analysis (no LLM API key configured).")
            return self._analyze_claim_heuristic(claim, all_evidence)

    def _analyze_claim_llm(self, claim: Dict[str, Any], all_evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        claim_text = claim.get("claim", "")
        supporting = []
        contradicting = []

        if not all_evidence:
            return {
                "claim": claim_text,
                "supporting_evidence": [],
                "contradicting_evidence": [],
                "status": "insufficient"
            }

        # Filter snippets with minimal word overlap to reduce prompt size
        claim_words = set(re.findall(r"\w+", claim_text.lower()))
        relevant_evidence = []
        for ev in all_evidence:
            snippet_words = set(re.findall(r"\w+", ev["snippet"].lower()))
            if len(claim_words.intersection(snippet_words)) >= 2 or ev["paper_id"] in [e["paper_id"] for e in claim.get("evidence", [])]:
                relevant_evidence.append(ev)

        if not relevant_evidence:
            relevant_evidence = all_evidence[:5]

        evidence_text = "\n".join([f"[{idx+1}] Paper ID: {ev['paper_id']} | Snippet: {ev['snippet']}" for idx, ev in enumerate(relevant_evidence)])

        prompt = (
            f"Analyze the relationship between this claim and the evidence snippets below:\n"
            f"Claim: \"{claim_text}\"\n\n"
            f"Evidence Snippets:\n{evidence_text}\n\n"
            f"For each snippet [1], [2], etc., judge if it SUPPORTS or CONTRADICTS the claim, or if it is NEUTRAL/INSUFFICIENT.\n"
            f"Respond ONLY with a JSON object in this format:\n"
            f"{{\"supporting_indices\": [1, 2], \"contradicting_indices\": [3]}}"
        )
        system_prompt = "You are a scientific contradiction detector. Analyze evidence strictly and return structured JSON."

        response = self.llm_client.generate(prompt, system_prompt)
        parsed = False
        if response:
            try:
                # Extract JSON block
                json_str = response
                if "{" in json_str and "}" in json_str:
                    json_str = json_str[json_str.find("{"):json_str.rfind("}")+1]
                data = json.loads(json_str)

                supp_idx = data.get("supporting_indices", [])
                contra_idx = data.get("contradicting_indices", [])

                for idx, ev in enumerate(relevant_evidence, 1):
                    ev_entry = {
                        "paper_id": ev["paper_id"],
                        "snippet": ev["snippet"],
                        "source_url": ev["source_url"]
                    }
                    if idx in contra_idx:
                        contradicting.append(ev_entry)
                    elif idx in supp_idx or ev["paper_id"] in [e["paper_id"] for e in claim.get("evidence", [])]:
                        supporting.append(ev_entry)
                parsed = True
            except Exception as e:
                logger.warning(f"Failed to parse LLM contradiction response: {e}. Falling back to heuristic.")

        if not parsed:
            return self._analyze_claim_heuristic(claim, all_evidence)

        # Determine status
        if len(supporting) > 0 and len(contradicting) > 0:
            status = "mixed"
        elif len(supporting) > 0:
            status = "supported"
        elif len(contradicting) > 0:
            status = "contradicted"
        else:
            status = "insufficient"

        return {
            "claim": claim_text,
            "supporting_evidence": supporting,
            "contradicting_evidence": contradicting,
            "status": status
        }

    def _analyze_claim_heuristic(self, claim: Dict[str, Any], all_evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        supporting = []
        contradicting = []

        claim_text = claim.get("claim", "").lower()
        claim_words = set(re.findall(r"\w+", claim_text))

        for ev in all_evidence:
            snippet = ev["snippet"].lower()
            snippet_words = set(re.findall(r"\w+", snippet))
            
            # Check overlap
            if len(claim_words.intersection(snippet_words)) < 2:
                continue

            # Check for contradiction indicators
            has_contra = any(kw in snippet for kw in self.CONTRADICTION_KEYWORDS)
            has_supp = any(kw in snippet for kw in self.SUPPORTING_KEYWORDS)

            ev_entry = {
                "paper_id": ev["paper_id"],
                "snippet": ev["snippet"],
                "source_url": ev["source_url"]
            }

            if has_contra and not has_supp:
                contradicting.append(ev_entry)
            elif has_supp or ev["paper_id"] in [e["paper_id"] for e in claim.get("evidence", [])]:
                supporting.append(ev_entry)

        # Determine status
        if len(supporting) > 0 and len(contradicting) > 0:
            status = "mixed"
        elif len(supporting) > 0:
            status = "supported"
        elif len(contradicting) > 0:
            status = "contradicted"
        else:
            status = "insufficient"

        return {
            "claim": claim["claim"],
            "supporting_evidence": supporting,
            "contradicting_evidence": contradicting,
            "status": status
        }
