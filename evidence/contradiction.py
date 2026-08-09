"""
Contradiction Detection and Analysis module.
Analyzes evidence for agreement, disagreement, and inconclusive status across papers.
"""

import re
import logging
from typing import List, Dict, Any

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

    def analyze_claim(self, claim: Dict[str, Any], all_evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze evidence items against a claim to detect agreement or disagreement."""
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
