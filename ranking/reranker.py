"""
Reranker module for scoring and ordering retrieved documents.
Implements BM25 keyword relevance with title match boosting.
"""

import math
import re
import logging
from typing import List
from retrieval.base import Document

logger = logging.getLogger(__name__)


class Reranker:
    """BM25 relevance scoring reranker with title match priority."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def rerank(self, query: str, documents: List[Document], top_k: int = 10) -> List[Document]:
        """Rank documents using BM25 relevance score + exact title similarity boost."""
        if not documents:
            return []

        query_terms = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 1]
        if not query_terms:
            return documents[:top_k]

        # Calculate average document length
        doc_lengths = [len(re.findall(r"\w+", doc.content)) for doc in documents]
        avg_dl = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1.0

        # Calculate document frequencies
        df = {}
        for term in set(query_terms):
            df[term] = sum(1 for doc in documents if term in doc.content.lower())

        num_docs = len(documents)

        scored_docs = []
        for idx, doc in enumerate(documents):
            doc_terms = [w.lower() for w in re.findall(r"\w+", doc.content)]
            dl = len(doc_terms)
            score = 0.0

            # BM25 Score
            for term in query_terms:
                if term not in df or df[term] == 0:
                    continue
                tf = doc_terms.count(term)
                idf = math.log((num_docs - df[term] + 0.5) / (df[term] + 0.5) + 1.0)
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (dl / avg_dl))
                score += idf * (numerator / denominator)

            # Title Match Boost
            clean_title_words = set(re.findall(r"\w+", doc.title.lower()))
            clean_query_words = set(query_terms)
            overlap = len(clean_title_words.intersection(clean_query_words))
            if overlap > 0:
                title_similarity = overlap / max(len(clean_query_words), 1)
                score += title_similarity * 15.0  # Heavy boost for title matches

            doc.metadata["bm25_score"] = round(score, 4)
            scored_docs.append((score, doc))

        # Sort descending by score
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        ranked = [doc for score, doc in scored_docs[:top_k]]
        
        logger.info(f"Reranked {len(documents)} documents -> top {len(ranked)} documents.")
        return ranked
