# Research Agent

**Research Agent** is an evidence-backed scientific research workspace designed to help users investigate scientific questions, discover relevant literature, retrieve supporting evidence, verify claims, and generate citation-grounded research syntheses.

The goal is to make literature research more structured, traceable, and reproducible by connecting retrieval, ranking, evidence extraction, claim verification, and synthesis in a single workflow.

## Features

- **Scientific research queries** — investigate research questions and hypotheses from a single workspace.
- **Evidence-backed answers** — generate findings grounded in retrieved scientific sources.
- **Hybrid retrieval** — combine dense retrieval with BM25 lexical search for relevant literature discovery.
- **Source ranking** — prioritize the most relevant papers before evidence extraction.
- **Evidence extraction** — identify passages and information that directly support research claims.
- **Claim verification** — connect claims to supporting evidence instead of presenting unsupported conclusions.
- **Citation-grounded synthesis** — produce research summaries linked to their underlying sources.
- **Source filtering** — work with sources such as arXiv and academic web results.
- **Research history** — keep previous research queries organized for quick access.
- **Light / dark mode** — responsive interface with a research-focused visual design.
- **Responsive UI** — designed for desktop and smaller screens.

## Research Workflow

```text
Research Question
       ↓
    Retrieve
       ↓
      Rank
       ↓
 Extract Evidence
       ↓
 Analyze Claims
       ↓
   Synthesize
       ↓
Evidence-Backed Result
```

Each stage is intended to make the final answer more transparent by preserving the relationship between a research claim and the evidence supporting it.

## Tech Stack

**Frontend**
- Next.js
- React
- TypeScript

**Backend**
- FastAPI
- Python
- LangGraph

**AI / Retrieval**
- Cohere Embed
- Cohere Rerank
- Cohere Command
- Qdrant
- BM25
- Reciprocal Rank Fusion (RRF)

## Project Architecture

```text
User Query
    │
    ▼
┌──────────────────┐
│ Research UI      │
│ Next.js / React  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Research API     │
│ FastAPI          │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────┐
│ Retrieval & Ranking         │
│ Dense + BM25 + RRF + Rerank │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│ Evidence & Claim Analysis   │
│ Extraction + Verification   │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│ Research Synthesis          │
│ Citations + Evidence        │
└─────────────────────────────┘
```

### 2. Configure environment variables

Create your local environment configuration using the provided `.env.example` file and add the required API keys and service configuration.

> Never commit API keys, tokens, or other secrets to the repository.

## Example Use Cases

Research Agent can be used for workflows such as:

- Investigating a scientific hypothesis
- Finding papers related to a research topic
- Comparing findings across multiple papers
- Extracting evidence from scientific literature
- Verifying whether a claim is supported by available sources
- Building citation-grounded literature summaries
- Exploring a new machine-learning or AI research area

## Evidence-First Design

Unlike a simple question-answering interface, Research Agent is designed around the relationship:

```text
Claim → Evidence → Source → Citation
```

This makes it easier to inspect where a finding came from and distinguish retrieved evidence from generated synthesis.

## Project Status

Research Agent is an actively developed research prototype. Retrieval, evidence extraction, claim verification, source management, and the research interface can be extended independently as the system evolves.

## Roadmap

- [ ] Improve multi-source retrieval
- [ ] Add stronger evidence scoring
- [ ] Improve claim-to-evidence linking
- [ ] Add richer paper metadata
- [ ] Improve research history management
- [ ] Add exportable research reports
- [ ] Add evaluation benchmarks for retrieval and grounding
- [ ] Improve citation quality and source coverage

## Contributing

Contributions and ideas are welcome. Open an issue to discuss a bug, feature request, or research workflow improvement before submitting a pull request.
