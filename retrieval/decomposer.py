"""
Dynamic Query Decomposition and Planning module.
Converts high-level user questions into targeted search queries across domains.
"""

import re
import logging
from typing import List

logger = logging.getLogger(__name__)


class QueryDecomposer:
    """Dynamic query planner breaking down research questions into multi-faceted subqueries."""

    TECHNICAL_KEYWORDS = {"ocr", "model", "vlm", "transformer", "code", "neural", "rag", "retrieval", "dataset"}

    def decompose(self, user_query: str) -> List[str]:
        """Generate focused search subqueries dynamically based on query domain."""
        clean_query = user_query.strip()
        subqueries = [clean_query]  # Primary query

        words = [w for w in re.findall(r"\w+", clean_query) if len(w) > 2]
        query_terms_lower = set(w.lower() for w in words)

        # Check if technical/scientific or general topic
        is_technical = bool(query_terms_lower.intersection(self.TECHNICAL_KEYWORDS))

        if is_technical:
            sub_aspects = [
                "analysis and benchmark",
                "methodology overview",
                "evaluation metrics",
                "recent developments"
            ]
        else:
            sub_aspects = [
                "biography and background",
                "key developments 2025",
                "news and public statements",
                "analysis overview"
            ]

        base_topic = " ".join([w for w in words if w.lower() not in {"find", "best", "approaches", "for", "since", "the", "and"}])

        for aspect in sub_aspects:
            sq = f"{base_topic} {aspect}".strip()
            if sq not in subqueries:
                subqueries.append(sq)

        logger.info(f"Decomposed query '{user_query}' into {len(subqueries)} subqueries.")
        return subqueries[:4]
