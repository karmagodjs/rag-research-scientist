# RAG Research Scientist Agent

> A production-grade, evidence-grounded scientific research agent that queries live literature, normalizes documents, deduplicates pools, reranks relevance, extracts evidence snippets, calculates dynamic confidence, detects contradictions, builds NetworkX evidence graphs, and formulates evidence-backed research proposals.

---

## Architecture Overview

```text
User Research Question
        ↓
Query Planner / Decomposer
        ↓
Multi-Source Retrieval (ArXiv, Web, Semantic)
        ↓
Document Pool Normalization
        ↓
Deduplication (DOI / arXiv ID / Title Similarity)
        ↓
Reranker (BM25 / Cosine Relevance)
        ↓
Evidence Extraction (Passage snippet mapping)
        ↓
Claim Generation & Dynamic Confidence Calculation
        ↓
Contradiction Detection (Supported | Mixed | Contradicted | Insufficient)
        ↓
Evidence Graph (NetworkX Nodes & Edges)
        ↓
Research Synthesizer (Timeline, Gaps, "What to research next?")
        ↓
Report Generation (JSON & Markdown)
```

---

## Key Features

1. **Zero Hardcoded Claims or Fake Data:** All claims, evidence snippets, confidence scores, and next-step proposals are derived strictly from retrieved scientific documents. If retrieval fails, `RETRIEVAL_FAILURE` is explicitly reported.
2. **Dynamic Query Decomposition:** Automatically breaks complex research queries into targeted multi-aspect sub-queries.
3. **Pluggable Retrieval & Reranking:** Abstract `BaseRetriever` interface supporting ArXiv REST API, Web search, and Semantic TF-IDF indexing. Pluggable `Reranker` supporting BM25 and neural bi-encoders.
4. **Calculated Confidence Scores:** Confidence is computed dynamically based on source count, snippet relevance, publication recency, and absence of contradiction.
5. **NetworkX Evidence Graph:** Maps relationships (`supports`, `contradicts`, `provides_evidence`, `evaluates_claim`) between Query, Claim, Paper, and Evidence nodes.

---

## Installation & Setup

```bash
# Clone or navigate to the project directory
cd rag-research-scientist

# Create python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Copy .env.example
cp .env.example .env
```

---

## Execution Examples

### 1. Run Research Agent Query
```bash
python agent.py --query "Find the best approaches for OCR on low-resource Indic languages since 2024" --max-papers 20 --output report.json --markdown report.md
```

### 2. Run Benchmark Evaluation Suite
```bash
python agent.py --query "test" --evaluate
```

### 3. Run Unit Tests
```bash
python -m unittest discover tests
```

---

## Directory Structure

```text
rag-research-scientist/
├── agent.py               # Main CLI & Self-Improvement Loop Orchestrator
├── config.py              # System configuration & environment options
├── requirements.txt       # Dependencies
├── .env.example           # Environment template
├── README.md              # Documentation
│
├── retrieval/             # Multi-source retrieval & normalization
│   ├── base.py            # BaseRetriever & Document dataclass
│   ├── arxiv.py           # ArXiv REST API retriever
│   ├── web.py             # Tavily / DDG Web retriever
│   ├── semantic.py        # Semantic TF-IDF retriever
│   ├── dedup.py           # Deduplication (DOI/arXiv/Title Jaccard)
│   └── decomposer.py      # Dynamic query planner
│
├── ranking/
│   └── reranker.py        # Pluggable BM25 document reranker
│
├── evidence/              # Evidence, claim, & graph generation
│   ├── extractor.py       # Evidence snippet extractor
│   ├── claims.py          # Claim generator & confidence calculator
│   ├── contradiction.py   # Contradiction analyzer
│   └── graph.py           # NetworkX evidence graph builder
│
├── synthesis/             # Report & timeline synthesis
│   ├── report.py          # JSON & Markdown synthesizer
│   ├── timeline.py        # Metadata timeline generator
│   └── gaps.py            # Dynamic gap detector & next steps
│
├── evaluation/
│   └── evaluator.py       # Quantitative benchmark evaluator
│
├── tests/                 # Unit tests
│   ├── test_retrieval.py
│   ├── test_claims.py
│   └── test_graph.py
│
└── data/
    └── benchmark.json     # Benchmark evaluation questions
```
