
import math
import re
import logging
from typing import List
from retrieval.base import Document
from retrieval.query_utils import detect_exact_paper_query, calculate_title_score

logger = logging.getLogger(__name__)


class Reranker:

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def rerank(self, query: str, documents: List[Document], top_k: int = 10) -> List[Document]:
        if not documents:
            return []

        try:
            is_exact_query, clean_title_query, author_hint = detect_exact_paper_query(query)
            logger.info(f"[RETRIEVAL] query = '{query}'")
            logger.info(f"[EXACT QUERY DETECTED] {is_exact_query}")
        except Exception as e:
            logger.warning(f"Exact query detection failed: {e}. Falling back to standard search.")
            is_exact_query, clean_title_query, author_hint = False, query, None

        query_terms = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 1]


        doc_lengths = [len(re.findall(r"\w+", doc.content or "")) for doc in documents]
        avg_dl = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1.0


        df = {}
        for term in set(query_terms):
            df[term] = sum(1 for doc in documents if term in (doc.content or "").lower())

        num_docs = len(documents)

        scored_docs = []
        for idx, doc in enumerate(documents):
            doc_terms = [w.lower() for w in re.findall(r"\w+", doc.content or "")]
            dl = len(doc_terms)
            bm25_score = 0.0


            for term in query_terms:
                if term not in df or df[term] == 0:
                    continue
                tf = doc_terms.count(term)
                idf = math.log((num_docs - df[term] + 0.5) / (df[term] + 0.5) + 1.0)
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (dl / avg_dl))
                bm25_score += idf * (numerator / denominator)


            try:
                title_info = calculate_title_score(
                    query_title=clean_title_query if clean_title_query else query,
                    candidate_title=doc.title or "",
                    candidate_authors=doc.authors or [],
                    author_hint=author_hint
                )
                title_score = title_info.get("score", 0.0)
                exact_match = title_info.get("exact_match", False)
                near_exact = title_info.get("near_exact", False)
            except Exception as e:
                logger.warning(f"Title matching failed for '{doc.title}': {e}")
                title_score, exact_match, near_exact = 0.0, False, False


            if exact_match:
                final_score = 100.0 + title_score + (min(bm25_score, 10.0) / 10.0)
            elif near_exact:
                final_score = 50.0 + title_score + (min(bm25_score, 10.0) / 10.0)
            elif is_exact_query and title_score >= 0.8:
                final_score = 25.0 + title_score + (min(bm25_score, 10.0) / 10.0)
            else:
                sem_raw = doc.metadata.get("semantic_score") if doc.metadata else None
                if sem_raw is None and doc.metadata:
                    sem_raw = doc.metadata.get("score", 0.5)
                semantic_score = float(sem_raw) if isinstance(sem_raw, (int, float)) else 0.5
                
                # Normalize BM25 and semantic scores
                norm_bm25 = min(bm25_score, 10.0) / 10.0
                norm_sem = min(max(semantic_score, 0.0), 2.0) / 2.0

                source_bonus = 0.05 if doc.source in ("arXiv", "openalex", "crossref") else 0.0
                final_score = (0.40 * title_score) + (0.30 * norm_bm25) + (0.30 * norm_sem) + source_bonus

            if doc.metadata is None:
                doc.metadata = {}
            doc.metadata["bm25_score"] = round(bm25_score, 4)
            doc.metadata["title_score"] = round(title_score, 4)
            doc.metadata["semantic_score"] = round(doc.metadata.get("semantic_score", 0.0) if isinstance(doc.metadata.get("semantic_score"), (int, float)) else 0.0, 4)
            doc.metadata["final_score"] = round(final_score, 4)

            logger.info(
                f"[RANKING] title='{doc.title}', title_score={title_score:.2f}, "
                f"bm25_score={bm25_score:.2f}, final_score={final_score:.2f}"
            )
            scored_docs.append((final_score, doc))


        scored_docs.sort(key=lambda x: x[0], reverse=True)
        ranked = [doc for score, doc in scored_docs[:top_k]]

        logger.info(f"Reranked {len(documents)} documents -> top {len(ranked)} documents.")
        return ranked
