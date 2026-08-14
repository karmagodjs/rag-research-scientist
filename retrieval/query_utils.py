
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
    "evolution", "does", "always", "increasing", "impact", "effect", "vs",
    "versus", "question", "answering", "multi-hop", "state of the art"
}


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
