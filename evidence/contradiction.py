
import re
import json
import logging
from typing import List, Dict, Any, Optional
from evidence.llm_client import LLMClient

logger = logging.getLogger(__name__)


class ContradictionDetector:

    CHALLENGE_PATTERNS = [
        r"\b(fails? to (outperform|improve|generalize|scale|reduce))\b",
        r"\b(inferior to|worse than|underperforms?|degrades? performance)\b",
        r"\b(contradicts?|refutes?|challenges? (the claim|prior findings|previous results))\b",
        r"\b(no (significant )?(improvement|gain|reduction|difference))\b",
        r"\b(ineffective|inaccurate|does not (improve|reduce|solve|hold))\b",
        r"\b(struggles? with|falls? short of|negative results?)\b",
        r"\b(increases? (hallucination|error rate|latency|cost))\b"
    ]

    SUPPORTING_PATTERNS = [
        r"\b(outperforms?|improves?|surpasses?|superior to)\b",
        r"\b(state-of-the-art|effective(ly)?|significantly enhances?)\b",
        r"\b(reduces? (hallucination|error|latency|cost))\b",
        r"\b(robust(ly)?|achieves? (high|superior|better))\b",
        r"\b(demonstrates? (strong|promising|substantial))\b"
    ]

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client

    def analyze_claim(self, claim: Dict[str, Any], all_evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        use_llm = self.llm_client is not None and self.llm_client.is_available()
        if use_llm:
            logger.info(f"LLM mode active for contradiction analysis of claim: '{claim.get('claim', '')[:40]}...'")
            return self._analyze_claim_llm(claim, all_evidence)
        else:
            logger.info("Heuristic mode active for contradiction analysis (no LLM API key configured).")
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
                "status": "INSUFFICIENT"
            }

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
            f"Analyze the relationship between this scientific claim and the evidence snippets below:\n"
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

        if len(supporting) > 0 and len(contradicting) > 0:
            status = "MIXED"
        elif len(supporting) > 0:
            status = "SUPPORTED"
        elif len(contradicting) > 0:
            status = "CONTRADICTED"
        else:
            status = "INSUFFICIENT"

        return {
            "claim": claim_text,
            "supporting_evidence": supporting,
            "contradicting_evidence": contradicting,
            "status": status
        }

    def _stem(self, word: str) -> str:
        w = word.lower()
        for sfx in ("ing", "tion", "tions", "ies", "es", "ed", "s"):
            if w.endswith(sfx) and len(w) > len(sfx) + 2:
                return w[:-len(sfx)]
        return w

    def _analyze_claim_heuristic(self, claim: Dict[str, Any], all_evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        supporting = []
        contradicting = []

        claim_text = claim.get("claim", "").lower()
        claim_words = [w for w in re.findall(r"\w+", claim_text) if len(w) > 2]
        claim_stems = set(self._stem(w) for w in claim_words)
        claim_paper_ids = set(e["paper_id"] for e in claim.get("evidence", []))

        for ev in all_evidence:
            snippet = ev["snippet"].lower()
            snippet_words = [w for w in re.findall(r"\w+", snippet) if len(w) > 2]
            snippet_stems = set(self._stem(w) for w in snippet_words)
            overlap = len(claim_stems.intersection(snippet_stems))

            if overlap < 1 and ev["paper_id"] not in claim_paper_ids:
                continue

            has_challenge = any(re.search(pat, snippet, re.IGNORECASE) for pat in self.CHALLENGE_PATTERNS)
            has_support = any(re.search(pat, snippet, re.IGNORECASE) for pat in self.SUPPORTING_PATTERNS)

            ev_entry = {
                "paper_id": ev["paper_id"],
                "snippet": ev["snippet"],
                "source_url": ev["source_url"]
            }

            if has_challenge and ev["paper_id"] not in claim_paper_ids:
                contradicting.append(ev_entry)
            elif has_support or ev["paper_id"] in claim_paper_ids:
                supporting.append(ev_entry)

        if len(supporting) > 0 and len(contradicting) > 0:
            status = "MIXED"
        elif len(supporting) > 0:
            status = "SUPPORTED"
        elif len(contradicting) > 0:
            status = "CONTRADICTED"
        else:
            status = "INSUFFICIENT"

        return {
            "claim": claim.get("claim", ""),
            "supporting_evidence": supporting,
            "contradicting_evidence": contradicting,
            "status": status
        }
