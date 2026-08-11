"""
Query normalization, exact paper title detection, and title similarity utilities.
"""

import re
from typing import Tuple, Optional, List, Dict, Any

NOISE_WORDS = {
    "paper", "research paper", "find", "show me", "the paper", "paper:",
    "papers", "study", "article", "publication", "pdf", "arxiv"
}

EXPLORATORY_TERMS = {
    "recent", "advances", "challenges", "survey", "overview", "methods",
    "techniques", "papers about", "research on", "applications of",
    "benchmarks for", "how to", "best approaches", "compare", "evaluation",
    "empirical", "systematic", "future", "directions", "trends", "literature"
}


def normalize_title(text: str) -> str:
    """Clean and normalize title or query string for exact matching."""
    if not text:
        return ""
    text = text.lower().strip()
    # Strip quotes
    text = re.sub(r'^["\'\s]+|["\'\s]+$', '', text)
    # Strip noise prefix
    text = re.sub(r'^(paper\s*:\s*|find\s+paper\s+|show\s+me\s+|find\s+)', '', text, flags=re.IGNORECASE)
    # Strip trailing noise
    text = re.sub(r'\s+(paper|research paper|pdf|article)$', '', text, flags=re.IGNORECASE)
    # Strip punctuation except alphanumeric + spaces
    text = re.sub(r"[^\w\s]", "", text)
    return " ".join(text.split())


def detect_exact_paper_query(query: str) -> Tuple[bool, str, Optional[str]]:
    """
    Detect if query is an exact paper title query.
    Returns: (is_exact, cleaned_title, author_hint)
    """
    if not query:
        return False, "", None

    raw_query = query.strip()
    norm_query = normalize_title(raw_query)

    # Check for quotes
    is_quoted = (raw_query.startswith('"') and raw_query.endswith('"')) or \
                 (raw_query.startswith("'") and raw_query.endswith("'"))

    # Check for prefix "paper:" or "find paper"
    has_explicit_prefix = bool(re.search(r'^(paper:|find paper|show paper)', raw_query, re.IGNORECASE))

    # Check for author hint (e.g. "Vaswani Attention Is All You Need")
    author_hint = None
    known_authors = ["vaswani", "devlin", "he", "brown", "kaplan", "touvron", "radford", "dosovitskiy"]
    words = norm_query.split()

    if len(words) > 1 and words[0] in known_authors:
        author_hint = words[0]
        norm_query = " ".join(words[1:])

    # Check exploratory indicators
    raw_lower = raw_query.lower()
    is_exploratory = any(term in raw_lower for term in EXPLORATORY_TERMS)

    if is_exploratory and not is_quoted and not has_explicit_prefix:
        return False, norm_query, author_hint

    # Title query criteria:
    # 1. Quoted query
    # 2. Has explicit paper prefix
    # 3. Author hint present
    # 4. Specific non-generic title phrase (3+ words, capital letters in raw, no exploratory terms)
    is_title_like = False
    if is_quoted or has_explicit_prefix or author_hint is not None:
        is_title_like = True
    elif len(words) >= 3 and not is_exploratory and any(c.isupper() for c in raw_query):
        is_title_like = True

    return is_title_like, norm_query, author_hint


def calculate_title_score(query_title: str, candidate_title: str, candidate_authors: Optional[List[str]] = None, author_hint: Optional[str] = None) -> Dict[str, Any]:
    """Calculate granular title matching score."""
    q_norm = normalize_title(query_title)
    t_norm = normalize_title(candidate_title)

    if not q_norm or not t_norm:
        return {"exact_match": False, "near_exact": False, "score": 0.0, "author_match": False}

    exact_match = (q_norm == t_norm)
    
    # Near exact: query in title or title in query with > 0.75 length ratio
    len_ratio = min(len(q_norm), len(t_norm)) / max(len(q_norm), len(t_norm))
    near_exact = exact_match or ((q_norm in t_norm or t_norm in q_norm) and len_ratio >= 0.75)

    # Word-level overlap
    q_words = set(q_norm.split())
    t_words = set(t_norm.split())
    intersection = q_words.intersection(t_words)
    union = q_words.union(t_words)
    jaccard = len(intersection) / len(union) if union else 0.0
    token_overlap = len(intersection) / len(q_words) if q_words else 0.0

    # Author matching
    author_match = False
    if author_hint and candidate_authors:
        author_str = " ".join(candidate_authors).lower()
        if author_hint in author_str:
            author_match = True

    if exact_match:
        score = 1.0
    elif near_exact:
        score = 0.95
    elif token_overlap >= 0.8:
        score = 0.85
    else:
        score = 0.50 * jaccard + 0.50 * token_overlap

    if author_match:
        score = min(1.0, score + 0.1)

    return {
        "exact_match": exact_match,
        "near_exact": near_exact,
        "score": round(score, 4),
        "author_match": author_match,
        "jaccard": round(jaccard, 4),
        "token_overlap": round(token_overlap, 4)
    }
