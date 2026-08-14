
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
    "empirical", "systematic", "future", "directions", "trends", "literature",
    "evolution", "evolved", "does", "always", "increasing", "impact", "effect", "vs",
    "versus", "question", "answering", "multi-hop", "state of the art",
    "since", "after", "latest", "unexplored", "limitations", "what methods"
}


def extract_temporal_constraints(query: str) -> Dict[str, Any]:
    """
    Extract temporal constraints such as:
    - 'since 2024' -> min_year = 2024
    - 'after 2023' -> min_year = 2024
    - 'from 2024 to 2026' -> min_year = 2024, max_year = 2026
    - 'between 2023 and 2025' -> min_year = 2023, max_year = 2025
    - 'in 2024' -> min_year = 2024, max_year = 2024
    - 'recent' / 'latest' -> is_recent = True, min_year = 2023
    """
    if not query:
        return {
            "has_temporal_constraint": False,
            "min_year": None,
            "max_year": None,
            "is_recent": False,
            "matched_phrases": []
        }

    q_lower = str(query).lower()
    matched_phrases = []
    min_year = None
    max_year = None
    is_recent = False

    # 1. Range patterns: "from 2023 to 2026", "between 2023 and 2025", "2023-2026"
    range_match = re.search(r"\bfrom\s+(19\d\d|20\d\d)\s+to\s+(19\d\d|20\d\d)\b", q_lower)
    if range_match:
        min_year = int(range_match.group(1))
        max_year = int(range_match.group(2))
        matched_phrases.append(range_match.group(0))

    if not range_match:
        between_match = re.search(r"\bbetween\s+(19\d\d|20\d\d)\s+and\s+(19\d\d|20\d\d)\b", q_lower)
        if between_match:
            min_year = int(between_match.group(1))
            max_year = int(between_match.group(2))
            matched_phrases.append(between_match.group(0))

    # 2. Lower bound patterns: "since 2024", "after 2023"
    if min_year is None:
        since_match = re.search(r"\bsince\s+(19\d\d|20\d\d)\b", q_lower)
        if since_match:
            min_year = int(since_match.group(1))
            matched_phrases.append(since_match.group(0))

    if min_year is None:
        after_match = re.search(r"\bafter\s+(19\d\d|20\d\d)\b", q_lower)
        if after_match:
            min_year = int(after_match.group(1)) + 1
            matched_phrases.append(after_match.group(0))

    # 3. Specific year pattern: "in 2024"
    if min_year is None:
        in_match = re.search(r"\bin\s+(19\d\d|20\d\d)\b", q_lower)
        if in_match:
            min_year = int(in_match.group(1))
            max_year = int(in_match.group(1))
            matched_phrases.append(in_match.group(0))

    # 4. Keyword patterns: "recent", "latest"
    if re.search(r"\b(recent|latest|newest)\b", q_lower):
        is_recent = True
        matched_phrases.append("recent")
        if min_year is None:
            min_year = 2023

    has_constraint = (min_year is not None) or (max_year is not None) or is_recent

    return {
        "has_temporal_constraint": has_constraint,
        "min_year": min_year,
        "max_year": max_year,
        "is_recent": is_recent,
        "matched_phrases": matched_phrases
    }


def parse_publication_year(published_str: Optional[str]) -> Optional[int]:
    """
    Safely extract a 4-digit publication year from a date string, or return None.
    """
    if not published_str:
        return None
    match = re.search(r"\b(19\d\d|20\d\d)\b", str(published_str))
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def calculate_temporal_score(published_str: Optional[str], temporal_info: Dict[str, Any]) -> float:
    """
    Calculate a temporal relevance score [0.0, 1.0] for a paper.
    If the query has NO temporal constraint, returns 0.0 (no effect on ranking).
    If the paper satisfies the temporal constraint (e.g. >= 2024), returns a strong bonus (1.0).
    If older, returns a smaller background relevance score (e.g. 0.1 - 0.2) based on proximity.
    """
    if not temporal_info.get("has_temporal_constraint"):
        return 0.0

    min_yr = temporal_info.get("min_year")
    max_yr = temporal_info.get("max_year")
    paper_yr = parse_publication_year(published_str)

    if paper_yr is None:
        return 0.1  # Unknown year gets neutral minimal background score

    # Check range satisfaction
    if min_yr is not None and max_yr is not None:
        if min_yr <= paper_yr <= max_yr:
            return 1.0
        elif paper_yr < min_yr:
            diff = min_yr - paper_yr
            return max(0.0, 0.5 - (diff * 0.1))
        else:
            diff = paper_yr - max_yr
            return max(0.0, 0.8 - (diff * 0.1))

    # Check lower bound satisfaction (e.g. "since 2024")
    if min_yr is not None:
        if paper_yr >= min_yr:
            return 1.0
        else:
            diff = min_yr - paper_yr
            # 2023 when min is 2024 -> 0.35, 2022 -> 0.25, 2021 -> 0.15, 2016 -> 0.0
            return max(0.0, round(0.45 - (diff * 0.10), 2))

    return 0.5


def normalize_title(text: str) -> str:
    if not text:
        return ""
    text = str(text).lower().strip()

    text = re.sub(r'^["\'\s]+|["\'\s]+$', '', text)

    text = re.sub(r'^(paper\s*:\s*|find\s+paper\s+|show\s+me\s+|find\s+)', '', text, flags=re.IGNORECASE)

    text = re.sub(r'\s+(paper|research paper|pdf|article)$', '', text, flags=re.IGNORECASE)

    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def detect_exact_paper_query(query: str) -> Tuple[bool, str, Optional[str]]:
    try:
        if not query:
            return False, "", None

        raw_query = str(query).strip()
        norm_query = normalize_title(raw_query)

        is_quoted = (raw_query.startswith('"') and raw_query.endswith('"')) or \
                     (raw_query.startswith("'") and raw_query.endswith("'"))

        has_explicit_prefix = bool(re.search(r'^(paper:|find paper|show paper)', raw_query, re.IGNORECASE))

        author_hint = None
        known_authors = ["vaswani", "devlin", "he", "brown", "kaplan", "touvron", "radford", "dosovitskiy", "lecun", "bengio", "hinton"]
        words = norm_query.split()

        if len(words) > 1 and words[0] in known_authors:
            author_hint = words[0]
            norm_query = " ".join(words[1:])
            words = norm_query.split()

        raw_lower = raw_query.lower()
        is_exploratory = any(term in raw_lower for term in EXPLORATORY_TERMS) or "?" in raw_query

        if is_exploratory and not is_quoted and not has_explicit_prefix:
            return False, norm_query, author_hint

        is_title_like = False
        if is_quoted or has_explicit_prefix or author_hint is not None:
            is_title_like = True
        elif not is_exploratory and len(words) >= 1:
            # Acronyms (BERT, GPT, LoRA) or Title-Cased names (Attention Is All You Need)
            if len(words) == 1 and raw_query.isupper():
                is_title_like = True
            elif len(words) >= 2 and any(c.isupper() for c in raw_query):
                is_title_like = True

        return is_title_like, norm_query, author_hint
    except Exception:
        return False, str(query or "").strip().lower(), None


def calculate_title_score(query_title: str, candidate_title: str, candidate_authors: Optional[List[str]] = None, author_hint: Optional[str] = None) -> Dict[str, Any]:
    try:
        q_norm = normalize_title(query_title)
        t_norm = normalize_title(candidate_title)

        if not q_norm or not t_norm:
            return {"exact_match": False, "near_exact": False, "score": 0.0, "author_match": False}

        exact_match = (q_norm == t_norm)

        len_ratio = min(len(q_norm), len(t_norm)) / max(len(q_norm), len(t_norm))
        
        # Near exact: contained with high len ratio, or candidate starts with query as distinct prefix (e.g. "BERT: ...")
        q_words = q_norm.split()
        t_words_list = t_norm.split()
        is_prefix = False
        if len(q_words) == 1 and len(t_words_list) > 0 and t_words_list[0] == q_words[0]:
            is_prefix = True
        elif len(q_words) > 1 and t_norm.startswith(q_norm):
            is_prefix = True

        near_exact = exact_match or ((q_norm in t_norm or t_norm in q_norm) and len_ratio >= 0.75) or is_prefix

        q_words_set = set(q_words)
        t_words_set = set(t_words_list)
        intersection = q_words_set.intersection(t_words_set)
        union = q_words_set.union(t_words_set)
        jaccard = len(intersection) / len(union) if union else 0.0
        token_overlap = len(intersection) / len(q_words_set) if q_words_set else 0.0

        author_match = False
        if author_hint and candidate_authors:
            author_str = " ".join([str(a) for a in candidate_authors if a]).lower()
            if author_hint in author_str:
                author_match = True

        if exact_match:
            score = 1.0
        elif is_prefix and len(q_words) == 1:
            score = 0.96
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
    except Exception:
        return {"exact_match": False, "near_exact": False, "score": 0.0, "author_match": False}
