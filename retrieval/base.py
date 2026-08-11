
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import datetime


@dataclass
class Document:
    id: str
    title: str
    authors: List[str]
    abstract: str
    url: str
    published: str  

    source: str     

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

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> List[Document]:
        pass
