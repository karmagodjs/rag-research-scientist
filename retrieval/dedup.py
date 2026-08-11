
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

    def deduplicate(self, documents: List[Document]) -> List[Document]:
        unique_docs: List[Document] = []
        seen_doi = set()
        seen_arxiv = set()

        for doc in documents:

            if doc.doi and doc.doi in seen_doi:
                logger.debug(f"Duplicate DOI detected: {doc.doi}")
                continue


            if doc.arxiv_id and doc.arxiv_id in seen_arxiv:
                logger.debug(f"Duplicate arXiv ID detected: {doc.arxiv_id}")
                continue


            norm_title = self._normalize_title(doc.title)
            is_dup = False
            for u_doc in unique_docs:
                u_norm_title = self._normalize_title(u_doc.title)
                sim = self._jaccard_similarity(norm_title, u_norm_title)
                if sim >= self.threshold:
                    logger.debug(f"Duplicate title similarity ({sim:.2f}): '{doc.title}' vs '{u_doc.title}'")
                    is_dup = True
                    break

            if not is_dup:
                unique_docs.append(doc)
                if doc.doi:
                    seen_doi.add(doc.doi)
                if doc.arxiv_id:
                    seen_arxiv.add(doc.arxiv_id)

        logger.info(f"Deduplicated {len(documents)} raw documents -> {len(unique_docs)} unique documents.")
        return unique_docs
