
import logging
from typing import List, Dict, Any
from retrieval.base import Document

logger = logging.getLogger(__name__)


class TimelineGenerator:

    def generate_timeline(self, documents: List[Document]) -> Dict[str, List[Dict[str, Any]]]:
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


        sorted_timeline = {k: timeline[k] for k in sorted(timeline.keys())}
        logger.info(f"Generated research timeline across {len(sorted_timeline)} publication years.")
        return sorted_timeline
