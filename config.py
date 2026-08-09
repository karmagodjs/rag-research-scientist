"""
Configuration settings for RAG Research Scientist Agent.
Loads settings from environment variables and CLI parameters.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentConfig:
    """Agent configuration options."""
    max_papers: int = 30
    top_k_rerank: int = 10
    max_iterations: int = 2
    timeout_seconds: int = 15
    arxiv_api_url: str = "https://export.arxiv.org/api/query"
    web_search_api_key: Optional[str] = field(default_factory=lambda: os.getenv("WEB_SEARCH_API_KEY"))
    tavily_api_key: Optional[str] = field(default_factory=lambda: os.getenv("TAVILY_API_KEY"))
    output_path: Optional[str] = "report.json"
    markdown_output_path: Optional[str] = "report.md"
    verbose: bool = False
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


default_config = AgentConfig()
