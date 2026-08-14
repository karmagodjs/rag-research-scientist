# -*- coding: utf-8 -*-
"""
Aspect-Aware Grounded Evidence Extraction Module
Extracts factual evidence snippets from retrieved academic abstracts and verified sources.
Scores sentence-level relevance using query alignment, aspect classification,
assertion strength, and document ranking signals.
"""

import re
import logging
from typing import List, Dict, Any
from retrieval.base import Document

logger = logging.getLogger(__name__)


class EvidenceExtractor:

    ASPECT_PATTERNS = {
        "limitations": r"\b(limitation|limitations|bottleneck|bottlenecks|degrad|struggl|error|challenge|challenges|failure mode|deficit|scarcity|vulnerab|lack of)\b",
        "methods": r"\b(propose|method|methods|model|models|framework|approach|architecture|technique|pipeline|transformer|vlm|fine-tun|decoder|encoder|layer)\b",
        "evolution": r"\b(evolv|since\s+\d{4}|recent|advances|progress|transition|shift|history|trend|emerging|new paradigm)\b",
        "findings": r"\b(achieve|achieves|outperform|outperforms|improve|improves|accuracy|state-of-the-art|sota|results|benchmark|score|f1|bleu|evaluat|demonstrat)\b",
        "future_directions": r"\b(future work|unexplored|research direction|open problem|open gap|promising|opportunity|future research)\b"
    }

    def extract_evidence(self, documents: List[Document], topic: str) -> List[Dict[str, Any]]:
        if not documents:
            return []

        evidence_list = []
        topic_words = set(w.lower() for w in re.findall(r"\w+", topic) if len(w) > 2)

        # Detect which aspects the user's research topic is asking about
        t_lower = topic.lower()
        query_aspects = set()
        if re.search(r"\b(evolv|since\s+\d{4}|recent|history|trend)\b", t_lower):
            query_aspects.add("evolution")
        if re.search(r"\b(methods?|perform best|sota|state of the art|approaches?)\b", t_lower):
            query_aspects.add("methods")
        if re.search(r"\b(limitations?|bottlenecks?|challenges?|failure modes?)\b", t_lower):
            query_aspects.add("limitations")
        if re.search(r"\b(unexplored|research directions?|future|gaps?)\b", t_lower):
            query_aspects.add("future_directions")

        for doc in documents:
            doc_title_words = set(w.lower() for w in re.findall(r"\w+", doc.title) if len(w) > 2)
            title_overlap_ratio = len(topic_words.intersection(doc_title_words)) / len(topic_words) if topic_words else 0.0

            # Document ranking score factor
            raw_final_score = doc.metadata.get("final_score", 0.5) if doc.metadata else 0.5
            doc_score_factor = 1.0 if raw_final_score >= 1.0 else min(1.0, max(0.2, float(raw_final_score)))

            source_type = "abstract" if doc.abstract else ("web_snippet" if doc.source == "web" else "metadata")
            text = f"{doc.title}. {doc.abstract}" if doc.abstract else (doc.content or doc.title)
            sentences = re.split(r"(?<=[.!?])\s+", text)

            for sentence in sentences:
                sentence_clean = sentence.strip()
                if len(sentence_clean) < 20:
                    continue

                s_words = set(w.lower() for w in re.findall(r"\w+", sentence_clean))
                overlap = len(topic_words.intersection(s_words))
                base_rel = overlap / len(topic_words) if topic_words else 0.4

                # Determine primary aspect of sentence
                primary_aspect = "findings"
                for aspect_name, pattern in self.ASPECT_PATTERNS.items():
                    if re.search(pattern, sentence_clean, re.IGNORECASE):
                        primary_aspect = aspect_name
                        break

                # If sentence or title has query relevance
                if overlap > 0 or title_overlap_ratio > 0.25:
                    finding_kws = {"propose", "show", "achieve", "demonstrate", "outperform", "find", "results", "model", "accuracy", "evaluate", "reduce", "increase", "improve", "benchmark"}
                    has_finding = bool(s_words.intersection(finding_kws))
                    finding_boost = 0.15 if has_finding else 0.0

                    # Boost if the snippet directly answers an aspect explicitly asked in user query
                    aspect_boost = 0.15 if (primary_aspect in query_aspects) else 0.0
                    title_boost = 0.15 if title_overlap_ratio > 0.3 else 0.0

                    rel_score = round(
                        min(1.0, max(0.15, (0.30 * base_rel) + (0.25 * doc_score_factor) + title_boost + finding_boost + aspect_boost)),
                        2
                    )

                    evidence_list.append({
                        "paper_id": doc.id,
                        "paper_title": doc.title,
                        "snippet": sentence_clean,
                        "source_url": doc.url,
                        "relevance_score": rel_score,
                        "aspect": primary_aspect,
                        "source_type": source_type,
                        "published_year": doc.published or "unknown",
                        "authors": doc.authors,
                    })

        # Sort by relevance score descending
        evidence_list.sort(key=lambda x: x["relevance_score"], reverse=True)
        logger.info(f"Extracted {len(evidence_list)} evidence snippets across {len(documents)} documents.")
        return evidence_list[:16]
