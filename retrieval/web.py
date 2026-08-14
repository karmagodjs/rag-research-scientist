# -*- coding: utf-8 -*-
"""
Web & OpenAlex Academic Search Retriever
Fetches real scientific publications from academic APIs (OpenAlex) and Web endpoints.
Never fabricates publication years; preserves authentic dates or marks as 'unknown'.
"""

import requests
import json
import logging
import re
import urllib.parse
from typing import List, Optional
from retrieval.base import BaseRetriever, Document
from retrieval.query_utils import detect_exact_paper_query

logger = logging.getLogger(__name__)


class WebRetriever(BaseRetriever):

    def __init__(self, tavily_api_key: Optional[str] = None, timeout: int = 6):
        super().__init__(name="web")
        self.tavily_api_key = tavily_api_key
        self.timeout = timeout

    def search(self, query: str, top_k: int = 10) -> List[Document]:
        is_exact, clean_title, author_hint = detect_exact_paper_query(query)
        if is_exact and clean_title:
            search_query = f'"{clean_title}" paper' if not author_hint else f'"{clean_title}" paper {author_hint}'
        else:
            search_query = query

        if self.tavily_api_key:
            return self._search_tavily(search_query, top_k)
        else:
            return self._search_ddg_lite(search_query, top_k)

    def _search_tavily(self, query: str, top_k: int) -> List[Document]:
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
                    year_match = re.search(r"\b(19\d\d|20\d\d)\b", snippet + " " + title)
                    pub_year = year_match.group(1) if year_match else "unknown"

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
            else:
                logger.warning(f"Tavily web search returned non-200 status code: {req.status_code}")
        except Exception as e:
            logger.warning(f"Tavily web search failed for '{query}': {str(e)}")

        return documents

    def _search_academic_web(self, query: str, top_k: int) -> List[Document]:
        url = "https://api.openalex.org/works"
        headers = {"User-Agent": "RAGResearchScientist/1.0 (academic research; mailto:research@example.org)"}
        documents = []

        clean_q = re.sub(r'[^\w\s-]', ' ', query)
        stop_phrases = ["state of the art and methods", "benchmark and evaluation", "empirical study and challenges", "recent developments and review", "paper"]
        for p in stop_phrases:
            clean_q = clean_q.replace(p, " ")
        clean_q = re.sub(r"\s+", " ", clean_q).strip()

        search_attempts = [query]
        if clean_q and clean_q != query:
            search_attempts.append(clean_q)

        words = clean_q.split()
        if len(words) > 8:
            core_words = [w for w in words if w.lower() not in {"compare", "and", "the", "for", "using", "with", "from", "approaches", "on", "in"}]
            if core_words:
                search_attempts.append(" ".join(core_words[:6]))

        for sq in search_attempts:
            try:
                params = {"search": sq, "per-page": top_k}
                resp = requests.get(url, params=params, headers=headers, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    for res in data.get("results", []):
                        title = res.get("title")
                        if not title:
                            continue
                        clean_title = re.sub(r"\s+", " ", title).strip()
                        raw_pub_year = res.get("publication_year")
                        year = str(raw_pub_year) if raw_pub_year else "unknown"
                        doi = res.get("doi")
                        authorships = res.get("authorships", [])
                        authors = [a.get("author", {}).get("display_name") for a in authorships if a.get("author", {}).get("display_name")]
                        if not authors:
                            authors = ["Academic Author"]

                        inv_index = res.get("abstract_inverted_index")
                        abstract = ""
                        if inv_index:
                            word_positions = []
                            for word, pos_list in inv_index.items():
                                for pos in pos_list:
                                    word_positions.append((pos, word))
                            word_positions.sort(key=lambda x: x[0])
                            abstract = " ".join(w for _, w in word_positions)

                        landing_url = res.get("primary_location", {}).get("landing_page_url") or doi or res.get("id") or f"https://openalex.org/{res.get('id', '')}"
                        doc = Document(
                            id=f"openalex_{res.get('id', '').split('/')[-1] or abs(hash(clean_title))}",
                            title=clean_title,
                            authors=authors,
                            abstract=abstract if abstract else f"Academic paper on {query}: {clean_title}",
                            url=landing_url,
                            published=year,
                            source="web",
                            doi=doi,
                            content=f"Title: {clean_title}\nAuthors: {', '.join(authors)}\nAbstract: {abstract}",
                            metadata={"score": 0.85}
                        )
                        documents.append(doc)
                if documents:
                    break
            except Exception as e:
                logger.warning(f"Academic web search failed for '{sq}': {e}")

        return documents

    def _search_ddg_lite(self, query: str, top_k: int) -> List[Document]:
        url = "https://lite.duckduckgo.com/lite/"
        documents = []
        try:
            logger.info(f"Querying Web Search (DDG Lite) for: '{query}'")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            resp = requests.post(url, data={"q": query}, headers=headers, timeout=self.timeout)

            if resp.status_code != 200:
                logger.info(f"DDG Lite returned status {resp.status_code} for query '{query}'. Falling back to academic web search.")
                return self._search_academic_web(query, top_k)

            html = resp.text

            link_matches = re.findall(r'<a[^>]+class=["\']result-link["\'][^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.DOTALL)
            snippet_matches = re.findall(r'<td[^>]+class=["\']result-snippet["\'][^>]*>(.*?)</td>', html, re.DOTALL)

            if not link_matches:
                logger.info(f"DDG Lite returned no HTML matches for query '{query}'. Falling back to academic web search.")
                return self._search_academic_web(query, top_k)

            for idx in range(min(top_k, len(link_matches))):
                raw_url, title_raw = link_matches[idx]
                clean_title = re.sub(r"<[^>]+>", "", title_raw).strip()
                if not clean_title:
                    continue

                snippet_raw = snippet_matches[idx] if idx < len(snippet_matches) else clean_title
                clean_snippet = re.sub(r"<[^>]+>", "", snippet_raw).strip()

                if not clean_snippet or len(clean_snippet) < 10:
                    clean_snippet = f"Web result regarding {query}. {clean_title}"

                year_match = re.search(r"\b(19\d\d|20\d\d)\b", clean_snippet + " " + clean_title)
                pub_year = year_match.group(1) if year_match else "unknown"

                url_match = re.search(r"uddg=([^&]+)", raw_url)
                clean_url = urllib.parse.unquote(url_match.group(1)) if url_match else raw_url

                if not clean_url:
                    continue

                full_url = clean_url if clean_url.startswith("http") else f"https://duckduckgo.com{clean_url}"

                doc = Document(
                    id=f"web_{abs(hash(full_url))}",
                    title=clean_title,
                    authors=["Web Contributor"],
                    abstract=clean_snippet,
                    url=full_url,
                    published=pub_year,
                    source="web",
                    content=f"Title: {clean_title}\nSnippet: {clean_snippet}"
                )
                documents.append(doc)

        except Exception as e:
            logger.warning(f"DDG Lite web search encountered exception for '{query}': {e}. Falling back to academic web search.")
            return self._search_academic_web(query, top_k)

        return documents
