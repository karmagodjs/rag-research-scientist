"""
Web Search Retriever implementation using optional Tavily API or DuckDuckGo Lite / HTML search.
"""

import requests
import json
import logging
import re
import urllib.parse
from typing import List, Optional
from retrieval.base import BaseRetriever, Document

logger = logging.getLogger(__name__)


class WebRetriever(BaseRetriever):
    """Retriever for general web search results, news, and online documents."""

    def __init__(self, tavily_api_key: Optional[str] = None, timeout: int = 10):
        super().__init__(name="web")
        self.tavily_api_key = tavily_api_key
        self.timeout = timeout

    def search(self, query: str, top_k: int = 10) -> List[Document]:
        """Execute web search and convert results into normalized Documents."""
        if self.tavily_api_key:
            return self._search_tavily(query, top_k)
        else:
            return self._search_ddg_lite(query, top_k)

    def _search_tavily(self, query: str, top_k: int) -> List[Document]:
        """Search via Tavily API if key is provided in environment."""
        url = "https://api.tavily.com/search"
        payload = json.dumps({
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": top_k
        }).encode("utf-8")

        documents = []
        try:
            logger.info(f"Querying Tavily Web API for: {query}")
            req = requests.post(url, data=payload, headers={"Content-Type": "application/json"}, timeout=self.timeout)
            if req.status_code == 200:
                data = req.json()
                for idx, res in enumerate(data.get("results", [])):
                    url_str = res.get("url", "")
                    title = res.get("title", f"Web Result {idx+1}")
                    snippet = res.get("content", "")
                    
                    year_match = re.search(r"\b(202[0-6])\b", snippet + " " + title)
                    pub_year = year_match.group(1) if year_match else "2025"

                    doc = Document(
                        id=f"web_{abs(hash(url_str))}",
                        title=title,
                        authors=["Web Source"],
                        abstract=snippet,
                        url=url_str,
                        published=pub_year,
                        source="web",
                        content=f"Title: {title}\nSnippet: {snippet}",
                        metadata={"score": res.get("score", 0.0)}
                    )
                    documents.append(doc)
        except Exception as e:
            logger.error(f"Tavily web search failed for '{query}': {str(e)}")

        return documents

    def _search_ddg_lite(self, query: str, top_k: int) -> List[Document]:
        """DuckDuckGo Lite search for robust general web query retrieval."""
        url = "https://lite.duckduckgo.com/lite/"
        documents = []
        try:
            logger.info(f"Querying Web Search (DDG Lite) for: '{query}'")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            resp = requests.post(url, data={"q": query}, headers=headers, timeout=self.timeout)
            html = resp.text

            # Extract links, titles, and snippets from DDG Lite HTML tables
            # Pattern matching title link: <a class="result-link" href="...">Title</a>
            # Pattern matching snippet: <td class="result-snippet">Snippet</td>
            link_matches = re.findall(r'<a[^>]+class=["\']result-link["\'][^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.DOTALL)
            snippet_matches = re.findall(r'<td[^>]+class=["\']result-snippet["\'][^>]*>(.*?)</td>', html, re.DOTALL)

            for idx in range(min(top_k, len(link_matches))):
                raw_url, title_raw = link_matches[idx]
                clean_title = re.sub(r"<[^>]+>", "", title_raw).strip()
                
                snippet_raw = snippet_matches[idx] if idx < len(snippet_matches) else clean_title
                clean_snippet = re.sub(r"<[^>]+>", "", snippet_raw).strip()

                if not clean_snippet or len(clean_snippet) < 10:
                    clean_snippet = f"Web result regarding {query}. {clean_title}"

                # Extract year
                year_match = re.search(r"\b(202[0-6])\b", clean_snippet + " " + clean_title)
                pub_year = year_match.group(1) if year_match else "2025"

                # Clean redirect URL if needed
                url_match = re.search(r"uddg=([^&]+)", raw_url)
                clean_url = urllib.parse.unquote(url_match.group(1)) if url_match else raw_url

                doc = Document(
                    id=f"web_{abs(hash(clean_url))}",
                    title=clean_title,
                    authors=["Web Contributor"],
                    abstract=clean_snippet,
                    url=clean_url if clean_url.startswith("http") else f"https://duckduckgo.com{clean_url}",
                    published=pub_year,
                    source="web",
                    content=f"Title: {clean_title}\nSnippet: {clean_snippet}"
                )
                documents.append(doc)

        except Exception as e:
            logger.error(f"DDG Lite web search failed for '{query}': {str(e)}")

        return documents
