# RAG Research Scientist

> **Evidence before conclusions.**

An evidence-oriented research agent for investigating scientific questions across live literature.

RAG Research Scientist decomposes complex research questions, retrieves and normalizes scientific literature, reranks sources, extracts evidence, generates confidence-scored claims, analyzes contradictory evidence, constructs an evidence graph, identifies research gaps, and proposes evidence-backed directions for further investigation.

**Live Demo:** https://rag-research-scientist.vercel.app
**Repository:** https://github.com/karmagodjs/rag-research-scientist

---

## Why this exists

Most research assistants optimize for producing an answer.

This project optimizes for making the **evidence chain inspectable**.

Instead of:

```text
Question → Answer
```

the system follows:

```text
Question
   ↓
Query Decomposition
   ↓
Multi-Source Retrieval
   ↓
Document Normalization
   ↓
Deduplication
   ↓
Reranking
   ↓
Evidence Extraction
   ↓
Claim Analysis
   ↓
Contradiction Analysis
   ↓
Evidence Graph
   ↓
Research Gaps
   ↓
Next Research Directions
```

The goal is not to hide the research process behind a single generated response, but to expose how conclusions are connected to their underlying evidence.

---

## Core capabilities

### Research planning

Complex research questions are decomposed into targeted sub-queries covering different aspects of the problem.

### Multi-source retrieval

The retrieval layer supports multiple sources through a common retriever interface, including:

* arXiv
* Web search
* Semantic / TF-IDF retrieval

### Document normalization

Retrieved documents are normalized into a common representation before downstream processing.

### Deduplication

Candidate documents are deduplicated using identifiers and title similarity to reduce redundant evidence.

### Relevance ranking

Retrieved documents are reranked using relevance scoring, including BM25-style ranking and pluggable reranking strategies.

### Evidence extraction

The system extracts high-signal passages from retrieved documents and associates them with their source metadata.

### Claim generation

Claims are constructed from retrieved evidence rather than generated independently of the literature.

Each claim can include:

* supporting evidence
* source information
* relevance
* confidence
* support status

### Contradiction analysis

Evidence is analyzed for agreement and disagreement.

Supported outcomes include:

```text
SUPPORTED
MIXED
CONTRADICTED
INSUFFICIENT
```

### Evidence graph

The system constructs a NetworkX graph connecting research entities and their relationships.

Example relationships:

```text
Paper ── supports --→ Claim
Paper ── provides_evidence --→ Evidence
Evidence ── supports --→ Claim
Paper ── evaluates --→ Claim
Claim ── contradicts --→ Claim
```

### Research gap detection

The synthesis layer analyzes the retrieved evidence to identify areas where the existing literature appears incomplete.

### Research recommendations

The system proposes evidence-backed directions for further investigation based on identified gaps and existing literature.

### Structured reports

Research results can be exported as:

* JSON
* Markdown

---

## System architecture

```text
                         RESEARCH QUESTION
                                │
                                ▼
                     ┌─────────────────────┐
                     │  Query Decomposer   │
                     └──────────┬──────────┘
                                │
                                ▼
                  ┌──────────────────────────┐
                  │    Multi-Source Search   │
                  │                          │
                  │  arXiv · Web · Semantic  │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │ Document Normalization   │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │      Deduplication        │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │       Reranking           │
                  │    BM25 / relevance      │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │    Evidence Extraction   │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │    Claim Generation      │
                  │  + Confidence Estimation │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │ Contradiction Analysis   │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │    Evidence Graph        │
                  │        NetworkX          │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │       Synthesis          │
                  │                          │
                  │ Timeline · Gaps · Next   │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │    Research Report       │
                  │      JSON / Markdown     │
                  └──────────────────────────┘
```

---

## Research workflow

A typical investigation looks like:

```text
1. Ask a research question

2. Decompose the question into sub-queries

3. Retrieve candidate literature

4. Normalize and deduplicate documents

5. Rank sources by relevance

6. Extract supporting passages

7. Construct claims from evidence

8. Estimate claim confidence

9. Analyze contradictory evidence

10. Build the evidence graph

11. Identify research gaps

12. Generate evidence-backed next directions
```

---

## Project structure

```text
rag-research-scientist/
│
├── agent.py
├── config.py
├── requirements.txt
├── .env.example
├── README.md
│
├── retrieval/
│   ├── base.py
│   ├── arxiv.py
│   ├── web.py
│   ├── semantic.py
│   ├── dedup.py
│   └── decomposer.py
│
├── ranking/
│   └── reranker.py
│
├── evidence/
│   ├── extractor.py
│   ├── claims.py
│   ├── contradiction.py
│   └── graph.py
│
├── synthesis/
│   ├── report.py
│   ├── timeline.py
│   └── gaps.py
│
├── evaluation/
│   └── evaluator.py
│
├── tests/
│   ├── test_retrieval.py
│   ├── test_claims.py
│   └── test_graph.py
│
├── data/
│   └── benchmark.json
│
├── api/
│   └── ...
│
└── web/
    ├── index.html
    ├── app.js
    └── styles.css
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/karmagodjs/rag-research-scientist.git
cd rag-research-scientist
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it.

### Windows

```powershell
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your environment file:

```bash
cp .env.example .env
```

Configure the required API credentials in `.env` according to the retrievers enabled in your environment.

---

## Run a research investigation

Example:

```bash
python agent.py \
  --query "Find the best approaches for OCR on low-resource Indic languages since 2024" \
  --max-papers 20 \
  --output report.json \
  --markdown report.md
```

The resulting investigation contains structured research artifacts including claims, evidence, source metadata, contradictions, research gaps, and recommendations.

---

## Run the web interface

Start the local research server:

```bash
python server.py
```

Then open:

```text
http://localhost:8000
```

The web interface provides an investigation-oriented workspace with:

* research synthesis
* claim inspection
* evidence inspection
* literature browsing
* evidence graph exploration
* research-gap analysis
* next-research recommendations
* JSON / Markdown export

---

## API

The research server exposes the following endpoints:

```text
POST /api/research

GET /api/research/:id

GET /api/research/:id/claims

GET /api/research/:id/evidence

GET /api/research/:id/graph

GET /api/research/:id/papers

GET /api/research/:id/gaps
```

### Start an investigation

```http
POST /api/research
Content-Type: application/json
```

Example request:

```json
{
  "query": "OCR on low-resource Indic languages since 2024",
  "max_papers": 15,
  "iterations": 1
}
```

---

## Evaluation

The repository includes a benchmark/evaluation layer for assessing the research pipeline.

Run:

```bash
python agent.py --query "test" --evaluate
```

Run the unit test suite:

```bash
python -m unittest discover tests
```

---

## Design principles

### Evidence over fluency

A fluent answer is not sufficient.

The system prioritizes traceable evidence and source relationships.

### Explicit uncertainty

Confidence is treated as a property of the evidence available to the system, not as an absolute measure of truth.

### Contradictions are first-class data

Conflicting evidence should be visible rather than silently collapsed into a single conclusion.

### Research gaps must be evidence-derived

The system should not invent gaps simply because they sound plausible.

### Reproducible artifacts

Investigations can be exported into structured JSON and Markdown reports for further analysis and archival.

### Modular retrieval

Retrieval and ranking components are designed around replaceable interfaces so additional sources and ranking strategies can be introduced without rewriting the entire pipeline.

---

## What makes this different?

Traditional RAG systems commonly follow:

```text
Retrieve → Generate
```

This project expands the workflow into:

```text
Retrieve
   ↓
Rank
   ↓
Extract Evidence
   ↓
Generate Claims
   ↓
Check Contradictions
   ↓
Build Relationships
   ↓
Identify Gaps
   ↓
Propose Next Research
```

The central object is therefore not the generated answer.

It is the **evidence chain behind the answer**.

---

## Limitations

This project is an experimental research system and should not be treated as an autonomous scientific authority.

Important limitations include:

* retrieval quality depends on the configured sources
* source coverage is incomplete
* relevance scores are ranking signals, not truth scores
* confidence estimates are heuristic
* contradiction detection can miss subtle disagreements
* research-gap detection depends on the retrieved literature
* generated research directions require human evaluation

The system is intended to **assist research**, not replace researcher judgment.

---

## Roadmap

Potential future work:

* [ ] Persistent investigation storage
* [ ] More scientific literature sources
* [ ] Improved semantic reranking
* [ ] Citation-level verification
* [ ] More robust contradiction classification
* [ ] Interactive evidence graph exploration
* [ ] Research-history and investigation comparison
* [ ] Benchmark expansion
* [ ] Evaluation of retrieval and evidence-grounding quality
* [ ] Reproducible investigation snapshots
* [ ] Collaborative research workspaces

---

## Citation

If you use this project in research or experimentation, please reference the repository:

```bibtex
@software{rag_research_scientist,
  author = {Dhruv Kumar},
  title = {RAG Research Scientist},
  year = {2026},
  url = {https://github.com/karmagodjs/rag-research-scientist}
}
```

---

## License

See the repository license for usage and redistribution terms.

---

## Acknowledgements

This project builds on ideas and open-source tooling from the broader research ecosystem, including scientific literature APIs, information retrieval methods, NetworkX, and the open-source RAG community.

---

### Research principle

> **Evidence before conclusions.**
