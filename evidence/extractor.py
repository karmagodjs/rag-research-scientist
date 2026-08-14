
import re
import logging
from typing import List, Dict, Any
from retrieval.base import Document

logger = logging.getLogger(__name__)


class EvidenceExtractor:

    def extract_evidence(self, documents: List[Document], topic: str) -> List[Dict[str, Any]]:
        evidence_list = []

        topic_words = set(w.lower() for w in re.findall(r"\w+", topic) if len(w) > 2)

        for doc in documents:
            doc_title_words = set(w.lower() for w in re.findall(r"\w+", doc.title) if len(w) > 2)
            title_overlap_ratio = len(topic_words.intersection(doc_title_words)) / len(topic_words) if topic_words else 0.0

            source_type = "abstract" if doc.abstract else ("web_snippet" if doc.source == "web" else "metadata")
            text = f"{doc.title}. {doc.abstract}" if doc.abstract else doc.content or doc.title
            sentences = re.split(r"(?<=[.!?])\s+", text)

            for sentence in sentences:
                sentence_clean = sentence.strip()
                if len(sentence_clean) < 20:
                    continue

                s_words = set(w.lower() for w in re.findall(r"\w+", sentence_clean))
                overlap = len(topic_words.intersection(s_words))

                # If sentence or title has query relevance
                if overlap > 0 or title_overlap_ratio > 0.3:
                    base_rel = overlap / len(topic_words) if topic_words else 0.4
                    title_boost = 0.25 if title_overlap_ratio > 0.4 else 0.1

                    # Finding / empirical keyword boost
                    finding_kws = {"propose", "show", "achieve", "demonstrate", "outperform", "find", "results", "mechanism", "model", "accuracy", "evaluate", "reduce", "increase", "improve", "benchmark"}
                    has_finding = bool(s_words.intersection(finding_kws))
                    finding_boost = 0.15 if has_finding else 0.0

                    rel_score = round(min(1.0, max(0.1, base_rel + title_boost + finding_boost)), 2)

                    evidence_list.append({
                        "paper_id": doc.id,
                        "paper_title": doc.title,
                        "snippet": sentence_clean,
                        "source_url": doc.url,
                        "relevance_score": rel_score,
                        "source_type": source_type,
                        "published_year": doc.published,
                        "authors": doc.authors,
                    })

        evidence_list.sort(key=lambda x: x["relevance_score"], reverse=True)
        logger.info(f"Extracted {len(evidence_list)} evidence snippets across {len(documents)} documents.")
        return evidence_list[:15]
