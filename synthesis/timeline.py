"""
Research Timeline Generator module.
Structures chronological milestones from actual document metadata.
"""

import logging
from typing import List, Dict, Any
from retrieval.base import Document

logger = logging.getLogger(__name__)


class TimelineGenerator:
    """Generates chronologically ordered timeline of research milestones from retrieved paper metadata."""

    def generate_timeline(self, documents: List[Document]) -> Dict[str, List[Dict[str, Any]]]:
        """Group documents by publication year and create chronological timeline."""
        timeline: Dict[str, List[Dict[str, Any]]] = {}

        for doc in documents:
            year = str(doc.published)[:4]
            if not year or not year.isdigit():
                year = "2025"

            if year not in timeline:
                timeline[year] = []

            timeline[year].append({
                "paper_id": doc.id,
                "title": doc.title,
                "authors": doc.authors[:2],
                "url": doc.url,
                "source": doc.source
            })

        # Sort timeline years ascending
        sorted_timeline = {k: timeline[k] for k in sorted(timeline.keys())}
        logger.info(f"Generated research timeline across {len(sorted_timeline)} publication years.")
        return sorted_timeline
