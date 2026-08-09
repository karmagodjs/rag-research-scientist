"""
arXiv API Retriever module.
Queries the official arXiv REST API with exact title boosting, fallback keyword search, and HTTP rate limit handling.
"""

import requests
import xml.etree.ElementTree as ET
import urllib.parse
import time
import logging
import re
from typing import List, Optional
from retrieval.base import BaseRetriever, Document

logger = logging.getLogger(__name__)

ARXIV_API_URL = "https://export.arxiv.org/api/query"


class ArxivRetriever(BaseRetriever):
    """Retriever fetching academic preprints directly from the arXiv API."""

    def __init__(self, api_url: Optional[str] = None, timeout: int = 12):
        super().__init__(name="arxiv")
        self.api_url = api_url or ARXIV_API_URL
        self.timeout = timeout

    def search(self, query: str, top_k: int = 10) -> List[Document]:
        """Execute arXiv search using exact title matching and core term fallback."""
        clean_query = query.strip()
        
        # Try exact title search first if query looks like a paper title
        docs = self._fetch_arxiv(f'ti:"{clean_query}"', top_k)
        if docs:
            logger.info(f"Exact title match found on arXiv for '{clean_query}': {len(docs)} papers.")
            return docs

        # Fallback to topic search with clean core terms
        STOP_WORDS = {"find", "best", "approaches", "for", "since", "with", "from", "using", "paper", "study", "analysis"}
        words = [w for w in re.findall(r"\w+", clean_query) if len(w) > 2 and w.lower() not in STOP_WORDS]
        
        if not words:
            query_str = f'all:"{clean_query}"'
        else:
            # Join top terms with AND
            core_terms = words[:3]
            query_str = " AND ".join([f'all:{term}' for term in core_terms])

        return self._fetch_arxiv(query_str, top_k)

    def _fetch_arxiv(self, query_param: str, top_k: int) -> List[Document]:
        """Send GET request to arXiv REST API and parse Atom XML response."""
        params = {
            "search_query": query_param,
            "start": 0,
            "max_results": top_k,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }

        documents = []
        try:
            time.sleep(0.3)  # Rate limiting respect
            resp = requests.get(ARXIV_API_URL, params=params, timeout=self.timeout)
            
            if resp.status_code != 200:
                logger.warning(f"arXiv API returned status {resp.status_code}")
                return documents

            root = ET.fromstring(resp.text)
            ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

            for entry in root.findall("atom:entry", ns):
                arxiv_id_elem = entry.find("atom:id", ns)
                title_elem = entry.find("atom:title", ns)
                summary_elem = entry.find("atom:summary", ns)
                published_elem = entry.find("atom:published", ns)

                if title_elem is None or summary_elem is None:
                    continue

                raw_title = title_elem.text.strip().replace("\n", " ")
                clean_title = re.sub(r"\s+", " ", raw_title)
                
                raw_summary = summary_elem.text.strip().replace("\n", " ")
                clean_summary = re.sub(r"\s+", " ", raw_summary)

                arxiv_id = arxiv_id_elem.text.split("/abs/")[-1] if arxiv_id_elem is not None else ""
                published_year = published_elem.text[:4] if published_elem is not None else "2025"

                authors = []
                for author in entry.findall("atom:author", ns):
                    name_elem = author.find("atom:name", ns)
                    if name_elem is not None:
                        authors.append(name_elem.text)

                pdf_url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""

                doc = Document(
                    id=f"arxiv_{arxiv_id.replace('/', '_')}",
                    title=clean_title,
                    authors=authors if authors else ["arXiv Author"],
                    abstract=clean_summary,
                    url=pdf_url,
                    published=published_year,
                    source="arXiv",
                    content=f"Title: {clean_title}\nAuthors: {', '.join(authors)}\nAbstract: {clean_summary}",
                    metadata={"arxiv_id": arxiv_id}
                )
                documents.append(doc)

        except Exception as e:
            logger.error(f"Failed to query arXiv for '{query_param}': {str(e)}")

        return documents
