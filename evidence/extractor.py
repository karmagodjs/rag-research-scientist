"""
Evidence Extractor module.
Extracts relevant evidence snippets from document abstracts and contents mapped to source URLs.
"""

import re
import logging
from typing import List, Dict, Any
from retrieval.base import Document

logger = logging.getLogger(__name__)


class EvidenceExtractor:
    """Extracts verifiable evidence passages from documents for key sub-aspects."""

    def extract_evidence(self, documents: List[Document], topic: str) -> List[Dict[str, Any]]:
        """Extract evidence passages matching the research topic from candidate documents."""
        evidence_list = []

        topic_words = set(w.lower() for w in re.findall(r"\w+", topic) if len(w) > 2)

        # Check if there is an exact or strong title match in candidate documents
        top_title_match = False
        for doc in documents:
            doc_title_words = set(w.lower() for w in re.findall(r"\w+", doc.title) if len(w) > 2)
            if topic_words and len(topic_words.intersection(doc_title_words)) / len(topic_words) >= 0.7:
                top_title_match = True
                break

        for doc in documents:
            doc_title_words = set(w.lower() for w in re.findall(r"\w+", doc.title) if len(w) > 2)
            title_overlap_ratio = len(topic_words.intersection(doc_title_words)) / len(topic_words) if topic_words else 0.0

            # If an exact title match exists in the corpus, discount unrelated papers
            if top_title_match and title_overlap_ratio < 0.4:
                continue  # Skip unrelated papers when user searched for exact paper title

            text = f"{doc.title}. {doc.abstract}"
            sentences = re.split(r"(?<=[.!?])\s+", text)

            for sentence in sentences:
                sentence_clean = sentence.strip()
                if len(sentence_clean) < 25:
                    continue

                s_words = set(w.lower() for w in re.findall(r"\w+", sentence_clean))
                overlap = len(topic_words.intersection(s_words))

                if overlap > 0:
                    base_rel = overlap / len(topic_words) if topic_words else 0.5
                    # Boost score if title matches target query
                    title_boost = 0.3 if title_overlap_ratio > 0.5 else 0.0
                    rel_score = round(min(1.0, base_rel + title_boost + 0.2), 2)

                    evidence_list.append({
                        "paper_id": doc.id,
                        "paper_title": doc.title,
                        "snippet": sentence_clean,
                        "source_url": doc.url,
                        "relevance_score": rel_score,
                        "published_year": doc.published,
                        "authors": doc.authors,
                    })

        # Sort evidence by relevance score descending
        evidence_list.sort(key=lambda x: x["relevance_score"], reverse=True)
        logger.info(f"Extracted {len(evidence_list)} evidence snippets across {len(documents)} documents.")
        return evidence_list[:15]
