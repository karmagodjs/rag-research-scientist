# -*- coding: utf-8 -*-
"""
Query Decomposition Module
Breaks down complex scientific research prompts into aspect-aware subqueries.
Preserves original query as subquery 1 while extracting distinct research dimensions:
- Temporal evolution & recent progress
- State-of-the-art / best-performing methods
- Empirical limitations & failure modes
- Unexplored research gaps & future directions
"""

import re
import logging
from typing import List, Optional
from retrieval.query_utils import (
    detect_exact_paper_query,
    extract_temporal_constraints
)

logger = logging.getLogger(__name__)


class QueryDecomposer:

    BIOGRAPHY_KEYWORDS = {"biography", "who is", "life of", "memoir", "profile of"}

    def _extract_core_topic(self, query: str) -> str:
        """
        Extract the central scientific topic from a research prompt,
        stripping prompt boilerplate, question frames, and trailing question clauses.
        """
        text = query.strip()

        # Remove trailing question mark
        text = text.rstrip("?").strip()

        # Check for multi-clause prompt separated by comma or 'and what'
        first_clause = re.split(r'[,;]|\band\s+what\b|\bwhat\s+methods\b|\bwhat\s+limitations\b', text, flags=re.IGNORECASE)[0].strip()

        # Strip question prefix
        cleaned = re.sub(
            r'^(how\s+(has|is|are|do|does|were|was)|what\s+(is|are|were|was|methods|approaches)|why\s+(do|does|is|are)|does\s+|can\s+|investigate\s+|explore\s+|analyze\s+|find\s+evidence\s+for\s+|find\s+paper\s+:?|find\s+)',
            '',
            first_clause,
            flags=re.IGNORECASE
        ).strip()

        # Strip framing phrases like "the major unexplored research gaps in", "major challenges in", "recent advances in", etc.
        cleaned = re.sub(
            r'^(the\s+)?(major\s+|current\s+|key\s+)?(unexplored\s+|open\s+)?(research\s+)?(gaps?|challenges?|limitations?|bottlenecks?|advances?|developments?|methods?|approaches?)\s+(in|for|of|on|with)\s+',
            '',
            cleaned,
            flags=re.IGNORECASE
        ).strip()

        # Strip trailing temporal / aspect verbs like "evolved since 2024", "been used for", etc.
        cleaned = re.sub(r'\s+(evolved|developed|progressed)\s+since\s+\d{4}.*$', '', cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'\s+since\s+\d{4}.*$', '', cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'\s+(being\s+used\s+for|used\s+for)\s+', ' for ', cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'^(the\s+)', '', cleaned, flags=re.IGNORECASE).strip()

        return cleaned if len(cleaned) > 3 else first_clause

    def decompose(self, user_query: str) -> List[str]:
        clean_query = user_query.strip()
        if not clean_query:
            return []

        # 1. Exact paper lookup query
        is_exact, target_title, author_hint = detect_exact_paper_query(clean_query)
        if is_exact:
            subqueries = [clean_query]
            if target_title and target_title != clean_query.lower():
                subqueries.append(target_title)
            if author_hint and target_title:
                subqueries.append(f"{author_hint} {target_title}")
            subqueries.append(f'"{target_title}" paper')
            return list(dict.fromkeys(subqueries))[:3]

        # 2. Always preserve the original query as subquery 1
        subqueries = [clean_query]

        temporal_info = extract_temporal_constraints(clean_query)
        core_topic = self._extract_core_topic(clean_query)
        q_lower = clean_query.lower()

        # 3. Detect Complex Multi-Aspect / Level-6 Queries
        # e.g., "How has OCR for low-resource Indic languages evolved since 2024, what methods currently perform best, what limitations remain, and what research directions are still unexplored?"
        has_evolution_aspect = bool(re.search(r'\b(evolv|since\s+\d{4}|progress|trend|history|recent advances)\b', q_lower))
        has_methods_aspect = bool(re.search(r'\b(methods?|perform best|state of the art|sota|techniques?|approaches?)\b', q_lower))
        has_limitations_aspect = bool(re.search(r'\b(limitations?|bottlenecks?|challenges?|failure modes?|drawbacks?)\b', q_lower))
        has_gaps_aspect = bool(re.search(r'\b(unexplored|research directions?|future work|open gaps?|open problems?)\b', q_lower))

        multi_aspect_count = sum([has_evolution_aspect, has_methods_aspect, has_limitations_aspect, has_gaps_aspect])

        if multi_aspect_count >= 2:
            # Aspect 1: Evolution / Temporal
            if has_evolution_aspect:
                temporal_suffix = f"since {temporal_info['min_year']}" if temporal_info.get("min_year") else "recent developments"
                subqueries.append(f"Evolution of {core_topic} {temporal_suffix}")

            # Aspect 2: Best-performing methods
            if has_methods_aspect:
                subqueries.append(f"Best-performing {core_topic} methods state of the art")

            # Aspect 3: Limitations and challenges
            if has_limitations_aspect:
                subqueries.append(f"Current limitations and failure modes in {core_topic}")

            # Aspect 4: Open gaps and unexplored directions
            if has_gaps_aspect:
                subqueries.append(f"Open research gaps and unexplored directions in {core_topic}")

        # 4. Comparative Queries (e.g., "Compare GraphRAG, vector RAG, and long-context approaches", "Compare RAG with long-context LLMs")
        elif "compare" in q_lower or " vs " in q_lower or "versus" in q_lower:
            if "graphrag" in q_lower or "graph" in q_lower:
                subqueries.append(f"GraphRAG for {core_topic}")
            if "vector rag" in q_lower or "rag" in q_lower:
                subqueries.append(f"Retrieval Augmented Generation for {core_topic}")
            if "long-context" in q_lower or "long context" in q_lower:
                subqueries.append(f"Long-context LLMs for {core_topic}")
            subqueries.append(f"Comparison benchmark of {core_topic}")

        # 5. Contradiction / Hallucination / Factuality Queries
        # e.g., "Does Retrieval-Augmented Generation always reduce hallucinations in large language models? Find evidence supporting and contradicting this claim."
        elif "hallucinat" in q_lower or "reduce" in q_lower or "contradict" in q_lower:
            subqueries.append(f"{core_topic} reduction of hallucinations in large language models")
            subqueries.append(f"{core_topic} hallucination limitations and ungrounded generation failure cases")
            subqueries.append(f"Empirical evaluation of {core_topic} on factuality and accuracy")

        # 6. General Exploratory Research Queries
        else:
            topic = core_topic if core_topic and len(core_topic) <= len(clean_query) else clean_query

            if has_gaps_aspect or has_limitations_aspect:
                subqueries.append(f"{topic} limitations and challenges")
                subqueries.append(f"{topic} open research gaps and future directions")
                subqueries.append(f"{topic} benchmark and evaluation")
            else:
                if temporal_info.get("has_temporal_constraint") and temporal_info.get("min_year"):
                    subqueries.append(f"{topic} advances since {temporal_info['min_year']}")
                else:
                    subqueries.append(f"{topic} state of the art and methods")

                subqueries.append(f"{topic} benchmark and evaluation")
                subqueries.append(f"{topic} empirical study and challenges")

        # Deduplicate while strictly preserving subquery order
        unique_subqueries = []
        for sq in subqueries:
            clean_sq = " ".join(sq.split())
            if clean_sq and clean_sq not in unique_subqueries:
                unique_subqueries.append(clean_sq)

        logger.info(f"Decomposed query '{user_query}' into {len(unique_subqueries)} subqueries.")
        return unique_subqueries[:4]
