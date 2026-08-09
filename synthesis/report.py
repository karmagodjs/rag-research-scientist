"""
Report Synthesizer module.
Synthesizes verified claims, evidence, timeline, gaps, and proposals into structured JSON and Markdown formats.
"""

import json
import logging
from typing import List, Dict, Any
from retrieval.base import Document

logger = logging.getLogger(__name__)


class ReportSynthesizer:
    """Synthesizes scientific reports in JSON and Markdown formats."""

    def build_full_report(
        self,
        query: str,
        documents: List[Document],
        claims: List[Dict[str, Any]],
        contradictions: List[Dict[str, Any]],
        evidence_graph: Dict[str, Any],
        timeline: Dict[str, List[Dict[str, Any]]],
        gaps: List[Dict[str, Any]],
        next_research: List[Dict[str, Any]],
        stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assemble all research components into unified JSON report."""
        report = {
            "research_question": query,
            "executive_summary": f"Scientific evidence synthesis for '{query}' compiled across {len(documents)} verified documents.",
            "retrieval_statistics": stats,
            "claims": claims,
            "contradiction_analysis": contradictions,
            "research_timeline": timeline,
            "open_research_gaps": gaps,
            "what_to_research_next": next_research,
            "evidence_graph": evidence_graph,
            "citation_list": [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "authors": doc.authors,
                    "url": doc.url,
                    "published": doc.published,
                    "source": doc.source
                } for doc in documents
            ]
        }
        return report

    def render_markdown(self, report_data: Dict[str, Any]) -> str:
        """Render JSON report into clear GitHub-flavored markdown."""
        md = []
        md.append(f"# Scientific Research Report: {report_data['research_question']}\n")
        md.append(f"**Executive Summary:** {report_data['executive_summary']}\n")

        # Stats
        stats = report_data.get("retrieval_statistics", {})
        md.append("## Retrieval Statistics")
        md.append(f"- Total Documents Analyzed: `{stats.get('total_documents', 0)}`")
        md.append(f"- Search Subqueries Executed: `{stats.get('num_subqueries', 0)}`")
        md.append(f"- Self-Improvement Iterations: `{stats.get('iterations', 1)}`\n")

        # Claims
        md.append("## Claims & Verified Evidence")
        for idx, claim in enumerate(report_data.get("claims", [])):
            md.append(f"### Claim {idx+1}: {claim['claim']}")
            md.append(f"- **Confidence Score:** `{claim['confidence'] * 100:.0f}%`")
            md.append(f"- **Reasoning:** {claim['reasoning']}")
            md.append("- **Supporting Evidence:**")
            for ev in claim.get("evidence", []):
                md.append(f"  - *\"{ev['snippet']}\"* — [{ev['paper_title']}]({ev['source_url']})")
            md.append("")

        # Contradictions
        md.append("## Contradiction Analysis")
        for contra in report_data.get("contradiction_analysis", []):
            md.append(f"- **Claim:** {contra['claim']}")
            md.append(f"  - **Status:** `{contra['status'].upper()}`")
            md.append(f"  - **Supporting Count:** {len(contra.get('supporting_evidence', []))}")
            md.append(f"  - **Contradicting Count:** {len(contra.get('contradicting_evidence', []))}\n")

        # Timeline
        md.append("## Research Timeline")
        for year, papers in report_data.get("research_timeline", {}).items():
            md.append(f"### {year}")
            for p in papers:
                md.append(f"- **{p['title']}** ({', '.join(p['authors'])}) — [Link]({p['url']})")
            md.append("")

        # Gaps
        md.append("## Open Research Gaps")
        for gap in report_data.get("open_research_gaps", []):
            md.append(f"### {gap['gap']}")
            md.append(f"- **Why It Matters:** {gap['why_it_matters']}")
            md.append("")

        # Next Research
        md.append("## What Should I Research Next?")
        for idx, rec in enumerate(report_data.get("what_to_research_next", [])):
            md.append(f"### Direction {idx+1}: {rec['research_direction']}")
            md.append(f"- **Motivation:** {rec['motivation']}")
            md.append(f"- **Novelty:** {rec['novelty']}")
            md.append(f"- **Difficulty:** `{rec['difficulty']}` | **Impact:** `{rec['expected_impact']}`\n")

        # Citations
        md.append("## Citation List")
        for cit in report_data.get("citation_list", []):
            md.append(f"- [{cit['id']}] **{cit['title']}** ({cit['published']}). [{cit['url']}]({cit['url']})")

        return "\n".join(md)
