
import requests
import xml.etree.ElementTree as ET
import urllib.parse
import logging
import re
from typing import List, Optional
from retrieval.base import BaseRetriever, Document
from retrieval.query_utils import detect_exact_paper_query

logger = logging.getLogger(__name__)

ARXIV_API_URL = "https://export.arxiv.org/api/query"


class ArxivRetriever(BaseRetriever):

    def __init__(self, api_url: Optional[str] = None, timeout: int = 6):
        super().__init__(name="arxiv")
        self.api_url = api_url or ARXIV_API_URL
        self.timeout = timeout

    def search(self, query: str, top_k: int = 10) -> List[Document]:
        clean_query = query.strip()
        is_exact, target_title, author_hint = detect_exact_paper_query(clean_query)

        documents = []

        STOP_WORDS = {"find", "best", "approaches", "for", "since", "with", "from", "using", "paper", "study", "analysis", "compare", "recent", "analyze", "investigate", "the", "a", "an", "of", "to", "in", "on", "is", "all", "you", "it", "and", "or", "are", "be", "that", "this", "which"}
        
        target = target_title if (is_exact and target_title) else clean_query
        all_words = [w for w in re.findall(r"\w+", target)]
        filtered_words = [w for w in all_words if len(w) > 2 and w.lower() not in STOP_WORDS]
        if not filtered_words:
            filtered_words = [w for w in all_words if len(w) > 1]

        if is_exact:
            # 1. Try exact title phrase search first
            exact_phrase_query = f'ti:"{target}"'
            exact_docs = self._fetch_arxiv(exact_phrase_query, top_k)
            documents.extend(exact_docs)

            # 2. Try title keyword search if exact phrase returned nothing
            if not documents and len(all_words) > 0:
                ti_terms = " AND ".join([f'ti:{w}' for w in (filtered_words[:4] if filtered_words else all_words[:4])])
                kw_docs = self._fetch_arxiv(ti_terms, top_k)
                documents.extend(kw_docs)

            # 3. If author hint is present, also query author + title
            if author_hint and filtered_words:
                au_docs = self._fetch_arxiv(f'au:{author_hint} AND ti:{filtered_words[0]}', top_k)
                documents.extend(au_docs)

            if len(documents) > 0:
                return self._dedup_internal(documents)[:top_k]

        # Broad search fallback
        core_terms = filtered_words[:4] if filtered_words else all_words[:3]
        query_str = " AND ".join([f'all:{term}' for term in core_terms]) if core_terms else f'all:"{clean_query}"'

        fallback_docs = self._fetch_arxiv(query_str, top_k)
        documents.extend(fallback_docs)

        return self._dedup_internal(documents)[:top_k]

    def _dedup_internal(self, docs: List[Document]) -> List[Document]:
        seen = set()
        unique = []
        for d in docs:
            if d.id not in seen:
                seen.add(d.id)
                unique.append(d)
        return unique

    def _fetch_arxiv(self, query_param: str, top_k: int) -> List[Document]:
        params = {
            "search_query": query_param,
            "start": 0,
            "max_results": top_k,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        headers = {
            "User-Agent": "rag-research-scientist/1.0 (academic research; contact@example.com)"
        }

        documents = []
        try:
            resp = requests.get(self.api_url, params=params, headers=headers, timeout=self.timeout)
            if resp.status_code == 429:
                logger.warning("[RETRIEVAL] arXiv rate limited: HTTP 429. Continuing without arXiv results for this subquery.")
                return []
            elif resp.status_code != 200:
                logger.warning(f"[RETRIEVAL] arXiv API returned HTTP status {resp.status_code}")
                return []

            if not resp.text or not resp.text.strip():
                return []

            root = ET.fromstring(resp.text)
            ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

            for entry in root.findall("atom:entry", ns):
                arxiv_id_elem = entry.find("atom:id", ns)
                title_elem = entry.find("atom:title", ns)
                summary_elem = entry.find("atom:summary", ns)
                published_elem = entry.find("atom:published", ns)

                if title_elem is None or summary_elem is None:
                    continue

                raw_title = title_elem.text.strip().replace("\n", " ") if title_elem.text else ""
                clean_title = re.sub(r"\s+", " ", raw_title)
                raw_summary = summary_elem.text.strip().replace("\n", " ") if summary_elem.text else ""
                clean_summary = re.sub(r"\s+", " ", raw_summary)

                if not clean_title:
                    continue

                arxiv_id = arxiv_id_elem.text.split("/abs/")[-1] if (arxiv_id_elem is not None and arxiv_id_elem.text) else ""
                published_year = published_elem.text[:4] if (published_elem is not None and published_elem.text) else "2025"

                authors = []
                for author in entry.findall("atom:author", ns):
                    name_elem = author.find("atom:name", ns)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text.strip())

                pdf_url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""

                doc = Document(
                    id=f"arxiv_{arxiv_id.replace('/', '_')}" if arxiv_id else f"arxiv_{abs(hash(clean_title))}",
                    title=clean_title,
                    authors=authors if authors else ["arXiv Author"],
                    abstract=clean_summary,
                    url=pdf_url,
                    published=published_year,
                    source="arXiv",
                    content=f"Title: {clean_title}\nAuthors: {', '.join(authors)}\nAbstract: {clean_summary}",
                    arxiv_id=arxiv_id if arxiv_id else None,
                    metadata={"arxiv_id": arxiv_id}
                )
                documents.append(doc)

        except Exception as e:
            logger.warning(f"arXiv API search failed for '{query_param}': {str(e)}. Returning empty list.")
            return []

        return documents
