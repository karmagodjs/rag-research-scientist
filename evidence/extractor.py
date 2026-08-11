
import re
import logging
from typing import List, Dict, Any
from retrieval.base import Document

logger = logging.getLogger(__name__)


class EvidenceExtractor:

    def extract_evidence(self, documents: List[Document], topic: str) -> List[Dict[str, Any]]:
        evidence_list = []

        topic_words = set(w.lower() for w in re.findall(r"\w+", topic) if len(w) > 2)


        top_title_match = False
        for doc in documents:
            doc_title_words = set(w.lower() for w in re.findall(r"\w+", doc.title) if len(w) > 2)
            if topic_words and len(topic_words.intersection(doc_title_words)) / len(topic_words) >= 0.7:
                top_title_match = True
                break

        for doc in documents:
            doc_title_words = set(w.lower() for w in re.findall(r"\w+", doc.title) if len(w) > 2)
            title_overlap_ratio = len(topic_words.intersection(doc_title_words)) / len(topic_words) if topic_words else 0.0


            if top_title_match and title_overlap_ratio < 0.4:
                continue  


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


        evidence_list.sort(key=lambda x: x["relevance_score"], reverse=True)
        logger.info(f"Extracted {len(evidence_list)} evidence snippets across {len(documents)} documents.")
        return evidence_list[:15]
