"""
Dynamic Query Decomposition and Planning module.
Converts high-level user research questions into targeted search subqueries across domains.
"""

import re
import logging
from typing import List

logger = logging.getLogger(__name__)


class QueryDecomposer:
    """Dynamic query planner breaking down research questions into multi-faceted subqueries."""

    BIOGRAPHY_KEYWORDS = {"biography", "who is", "life of", "memoir", "profile of"}

    def decompose(self, user_query: str) -> List[str]:
        """Generate focused search subqueries dynamically based on query domain."""
        clean_query = user_query.strip()
        from retrieval.query_utils import detect_exact_paper_query

        is_exact, target_title, author_hint = detect_exact_paper_query(clean_query)
        if is_exact:
            subqueries = [clean_query]
            if target_title and target_title != clean_query.lower():
                subqueries.append(target_title)
            if author_hint and target_title:
                subqueries.append(f"{author_hint} {target_title}")
            subqueries.append(f'"{target_title}" paper')
            return list(dict.fromkeys(subqueries))[:3]

        subqueries = [clean_query]
        words = [w for w in re.findall(r"\w+", clean_query) if len(w) > 2]
        query_terms_lower = set(w.lower() for w in words)

        # Check if query is explicitly asking for biographical information
        is_biographical = bool(query_terms_lower.intersection(self.BIOGRAPHY_KEYWORDS)) or any(k in clean_query.lower() for k in self.BIOGRAPHY_KEYWORDS)

        if is_biographical:
            sub_aspects = [
                "biography and background",
                "key achievements and contributions",
                "recent developments and updates",
                "overview and analysis"
            ]
        else:
            sub_aspects = [
                "state of the art and methods",
                "benchmark and evaluation",
                "empirical study and challenges",
                "recent developments and review"
            ]

        stop_words = {"find", "best", "approaches", "for", "since", "the", "and", "with", "from", "using", "study", "studies"}
        base_terms = [w for w in words if w.lower() not in stop_words]
        base_topic = " ".join(base_terms) if base_terms else clean_query

        for aspect in sub_aspects:
            sq = f"{base_topic} {aspect}".strip()
            if sq not in subqueries:
                subqueries.append(sq)

        logger.info(f"Decomposed query '{user_query}' into {len(subqueries)} subqueries.")
        return subqueries[:3]
