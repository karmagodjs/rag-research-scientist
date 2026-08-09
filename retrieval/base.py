"""
Base interfaces and data schemas for multi-source retrieval.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import datetime


@dataclass
class Document:
    """Normalized document schema across all retrieval sources."""
    id: str
    title: str
    authors: List[str]
    abstract: str
    url: str
    published: str  # YYYY or YYYY-MM-DD
    source: str     # arxiv, web, semantic, etc.
    content: str = ""
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "url": self.url,
            "published": self.published,
            "source": self.source,
            "content": self.content,
            "doi": self.doi,
            "arxiv_id": self.arxiv_id,
            "metadata": self.metadata,
        }


class BaseRetriever(ABC):
    """Abstract Base Class for document retrievers."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> List[Document]:
        """Search and return normalized Document objects."""
        pass
