
import re
import logging
from typing import List
from retrieval.base import Document

from retrieval.query_utils import normalize_title

logger = logging.getLogger(__name__)


class DocumentDeduplicator:

    def __init__(self, title_similarity_threshold: float = 0.85):
        self.threshold = title_similarity_threshold

    def _normalize_title(self, title: str) -> str:
        return normalize_title(title)

    def _jaccard_similarity(self, str1: str, str2: str) -> float:
        set1 = set(str1.split())
        set2 = set(str2.split())
        if not set1 or not set2:
            return 0.0
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union)

    def _doc_quality(self, doc: Document) -> float:
        score = 0.0
        # Abstract length and information content
        abs_len = len(doc.abstract or "")
        if abs_len > 200:
            score += 2.0
        elif abs_len > 50:
            score += 1.0

        # Concrete author names
        generic_authors = {"web source", "web contributor", "arxiv author", "academic author", "a", "b"}
        has_real_authors = any(a.lower() not in generic_authors for a in (doc.authors or []))
        if has_real_authors:
            score += 1.0

        # Identifier presence
        if doc.doi:
            score += 0.5
        if doc.arxiv_id:
            score += 0.5
        if doc.url and doc.url.startswith("http"):
            score += 0.5

        # Source reliability
        if doc.source == "arXiv":
            score += 1.0
        elif doc.source in ("openalex", "crossref"):
            score += 0.8
        else:
            score += 0.5

        # Semantic/relevance metadata score
        if doc.metadata:
            sem = doc.metadata.get("semantic_score") or doc.metadata.get("score") or 0.0
            if isinstance(sem, (int, float)):
                score += sem

        return score

    def deduplicate(self, documents: List[Document]) -> List[Document]:
        unique_docs: List[Document] = []

        for doc in documents:
            norm_title = self._normalize_title(doc.title)
            dup_idx = -1

            for idx, u_doc in enumerate(unique_docs):
                # Check exact DOI match
                if doc.doi and u_doc.doi and doc.doi.lower() == u_doc.doi.lower():
                    dup_idx = idx
                    break

                # Check exact arXiv ID match
                if doc.arxiv_id and u_doc.arxiv_id and doc.arxiv_id.strip() == u_doc.arxiv_id.strip():
                    dup_idx = idx
                    break

                # Check title similarity
                u_norm_title = self._normalize_title(u_doc.title)
                if norm_title and u_norm_title:
                    if norm_title == u_norm_title:
                        dup_idx = idx
                        break
                    sim = self._jaccard_similarity(norm_title, u_norm_title)
                    if sim >= self.threshold:
                        dup_idx = idx
                        break

            if dup_idx >= 0:
                # If duplicate detected, compare quality
                existing_doc = unique_docs[dup_idx]
                if self._doc_quality(doc) > self._doc_quality(existing_doc):
                    logger.debug(f"Replacing duplicate '{existing_doc.title}' with higher-quality candidate '{doc.title}'")
                    unique_docs[dup_idx] = doc
                else:
                    logger.debug(f"Keeping higher/equal-quality existing '{existing_doc.title}' over '{doc.title}'")
            else:
                unique_docs.append(doc)

        logger.info(f"Deduplicated {len(documents)} raw documents -> {len(unique_docs)} unique documents.")
        return unique_docs
