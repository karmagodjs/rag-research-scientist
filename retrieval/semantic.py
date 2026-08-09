"""
Semantic Retriever implementation using vector/TF-IDF similarity over local index or corpus.
"""

import math
import re
import logging
from typing import List, Dict
from retrieval.base import BaseRetriever, Document

logger = logging.getLogger(__name__)


class SemanticRetriever(BaseRetriever):
    """Semantic vector/TF-IDF retriever operating over a candidate Document pool."""

    def __init__(self, corpus: List[Document] = None):
        super().__init__(name="semantic")
        self.corpus: List[Document] = corpus or []

    def set_corpus(self, corpus: List[Document]):
        """Update candidate document corpus."""
        self.corpus = corpus

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def _tf_idf_score(self, query_terms: List[str], doc_text: str) -> float:
        doc_terms = self._tokenize(doc_text)
        if not doc_terms:
            return 0.0
        score = 0.0
        doc_len = len(doc_terms)
        for q in set(query_terms):
            tf = doc_terms.count(q) / doc_len
            if tf > 0:
                score += tf * math.log(1.5 + (1.0 / (tf + 0.1)))
        return score

    def search(self, query: str, top_k: int = 10) -> List[Document]:
        """Rank documents in the corpus semantically against query."""
        if not self.corpus:
            logger.info("SemanticRetriever corpus is empty.")
            return []

        query_terms = self._tokenize(query)
        scored_docs = []

        for doc in self.corpus:
            score = self._tf_idf_score(query_terms, f"{doc.title} {doc.abstract}")
            if score > 0.0:
                scored_docs.append((score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[:top_k]]
