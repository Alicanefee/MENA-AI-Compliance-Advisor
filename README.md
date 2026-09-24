# MENA AI Compliance Advisor

> **Source-grounded compliance support for companies adopting AI in the Middle East - starting with the UAE and Saudi Arabia, with EU rules for cross-border work.**
> Ask questions, track open cases and their documents in Excel, and train staff. Every statement must quote the official text, or it is not shown.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Status: v0.1.0](https://img.shields.io/badge/status-v0.1.0-orange.svg)](#roadmap)
[![Tests: pytest](https://img.shields.io/badge/tests-pytest-green.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> ⚠️ **Informational examples only - not legal advice.** Indexed texts may be outdated or unofficial translations, and curated content can contain errors. **All legal obligations arising from use of this software remain solely with the user.** See [DISCLAIMER.md](DISCLAIMER.md).

---

## What it does

| | |
|---|---|
| **Advise** | Answers questions about AI use (recruitment, monitoring, automated decisions, data transfers…) from the official texts of the UAE Labour Law and PDPL, the Saudi Labor Law, PDPL and its Implementing Regulations, the UAE AI Charter, SDAIA's AI Ethics Principles, the EU AI Act and the GDPR. |
| **Compare jurisdictions** | Filters or combines UAE, Saudi and EU sources, and keeps them apart in answers. |
| **Track cases** | Open-ended questions become cases in an Excel workbook (`Cases`, `Documents`, `Log` sheets) with a document checklist, uploads, overdue alerts and a mandatory named human reviewer for approval. |
| **Train** | Five modules, quizzes, learning paths and four practice scenarios, in English with Arabic titles and interface. Each legal point is automatically checked against the official text. |
| **Stay current** | Re-downloads sources, keeps previous versions and produces article-level diff reports (optionally with an AI summary). |

## How it limits hallucination and confirmation bias

| Mechanism | Implementation |
|---|---|
| **Official texts only** | Sources are downloaded from government sites listed in [`config/sources.yaml`](config/sources.yaml) and split into article-level passages. The model sees only the retrieved passages. |
| **Quote or drop** | The analyst agent must attach a verbatim quote and passage label to every finding. A deterministic verifier ([`agents/verifier.py`](compliance/agents/verifier.py)) drops any finding whose quote is not in the cited passage. No model checks another model's homework. |
| **Built-in dissent** | A separate challenger agent is prompted to argue against the draft: exceptions, scope limits (free zones, excluded data), narrower readings, other jurisdictions. Its counterpoints pass the same verifier; findings it disputes are shown as unresolved, not as conclusions. |
| **No free text** | The summary the user reads is assembled from verified findings by code, not written by the model. |
| **Abstain** | No matching provision → no answer. No LLM configured → the relevant provisions are shown without conclusions (extractive mode). |
| **Checked curated content** | Curriculum points, scenario answers and document rules carry `source + article + expected wording`. [`verify_content.py`](scripts/verify_content.py) checks them against the indexed text and the UI labels each one *confirmed / not confirmed / not indexed*. Law and good practice are labelled separately. |
| **Human in the loop** | Every answer is flagged for review; a case cannot be approved without a named reviewer. |

## Architecture

```
 official sites ──fetch_laws.py──▶ data/laws/raw ──build_index.py──▶ passages.jsonl (+ optional ChromaDB)
       ▲                                  │                                   │
 check_updates.py (diff reports)   ai_extract.py (Claude reads PDF;           ▼
                                   text-layer cross-check)           ┌──────────────────┐
                                                                     │ Retriever (BM25, │
 question ──▶ jurisdiction detection ──▶ retrieve ─────────────────▶ │  + vectors, RRF) │
                                                                     └────────┬─────────┘
          ┌───────────────────────────────────────────────────────────────────┘
          ▼
   Analyst agent ──▶ Challenger agent ──▶ Verifier (verbatim quotes) ──▶ Answer
   (findings+quotes)  (counterpoints,      (deterministic)                + document rules (YAML)
                       disputes)                                          + human review flag
          │
          ▼
   Case register (Excel)  ·  Training (YAML content, SQLite progress)  ·  FastAPI + web UI (EN/AR)
```

| Path | Role |
|---|---|
| `compliance/corpus/` | Source registry, download with version history, PDF/HTML extraction (incl. two-column pages), article chunker, AI transcription, update checks and diffs |
| `compliance/retrieval/` | BM25 (dependency-free), optional ChromaDB vectors, reciprocal-rank fusion |
| `compliance/agents/` | Analyst, challenger, verifier, document rules, orchestrator |
| `compliance/llm/` | Anthropic (default `claude-opus-5`, with server-side refusal fallbacks) and OpenAI providers |
| `compliance/cases/` | Excel case register |
| `compliance/education/` | Curriculum/scenario catalog and learner progress |
| `compliance/api/` | FastAPI app; serves the UI from `web/` |
| `config/` | Sources and document rules · `content/` curriculum and scenarios |

## Quick start

```bash
py -3.13 -m venv .venv            # Windows; use python3 -m venv .venv elsewhere
.venv\Scripts\activate            # source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
copy .env.example .env            # cp on macOS/Linux; set LLM_PROVIDER and an API key

python scripts/fetch_laws.py      # download official texts
python scripts/build_index.py     # extract, chunk, index
python scripts/verify_content.py  # check curated content against the texts
uvicorn compliance.api.main:app --reload
```

Open http://localhost:8000.

**Manual download.** `uaelegislation.gov.ae` blocks automated clients (HTTP 403). The fetcher does not work around this; it prints the page to open instead. Save the UAE PDPL from <https://uaelegislation.gov.ae/en/legislations/1972> as `data/laws/raw/uae_pdpl.pdf`, then rerun `build_index.py`.

**AI extraction.** The MOHRE edition of the UAE Labour Law prints two book pages per PDF page with headings after the article text, so article numbers cannot be read from the text layer. Until you run

```bash
python scripts/ai_extract.py uae_labour_law   # needs LLM_PROVIDER=anthropic
python scripts/build_index.py
```

that law is indexed page by page, and curriculum points citing its articles show as *not indexed*. The transcription is checked word-for-word against the PDF text layer. Articles whose wording is not found in the PDF are left out of the index. For scanned PDFs without a text layer (OCR), the result is indexed with an *unverified OCR* warning.

**Keeping laws current.**

```bash
python scripts/check_updates.py --status             # when was each source last checked
python scripts/check_updates.py --summarize --rebuild
```

Changed sources get a diff report in `data/laws/diffs/`, also available in the UI (Sources tab) and the API. [`.github/workflows/check-laws.yml`](.github/workflows/check-laws.yml) runs the check weekly.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `LLM_PROVIDER` | `none` | `none` (extractive), `anthropic` or `openai` |
| `LLM_MODEL` | provider default | `claude-opus-5` for Anthropic, `gpt-4o-mini` for OpenAI |
| `RETRIEVAL` | `bm25` | `hybrid` adds ChromaDB vectors (`pip install chromadb`, then `build_index.py --vector`) |
| `EMBEDDINGS` | `chroma-default` | or `openai` |
| `MIN_PASSAGE_SCORE` | `1.0` | BM25 score below which a passage is not used as evidence |
| `DATA_DIR` | `./data` | All generated data |

## API

| Method | Path | |
|---|---|---|
| `POST` | `/api/ask` | Question → verified findings, counterpoints, provisions, document checklist |
| `POST/GET/PATCH` | `/api/cases`, `/api/cases/{id}` | Create (optionally runs the advisor), list, view, review |
| `POST/PATCH` | `/api/cases/{id}/documents[/{doc_id}]`, `…/upload` | Document checklist and uploads |
| `GET/POST` | `/api/learn/modules`, `/api/learn/answer`, `/api/learn/scenarios…` | Training |
| `GET` | `/api/sources`, `/api/sources/{id}/diffs` | Source freshness and change reports |
| `POST` | `/api/sources/{id}/check?summarize=true` | Re-check one source now |

Interactive docs at `/docs`.

## Current content status

Against the official texts downloaded on 2026-09-24:

- **50** citations confirmed.
- **0** contradicted.
- **11** waiting for AI extraction of the UAE Labour Law.
- **22** waiting for the manual UAE PDPL download.

Run `verify_content.py` after every source update.

## Roadmap

- Reviewed Arabic translations of lesson and scenario text (titles, UI and disclaimer are already bilingual)
- More sources: DIFC/ADGM data protection, UAE health data law, sector regulators (CBUAE, SAMA)
- Consolidated EU AI Act text and tracking of amendments to application dates
- Authentication and per-user access for the case register
- Email reminders for overdue documents

## License

MIT - see [LICENSE](LICENSE). Use is subject to the [DISCLAIMER](DISCLAIMER.md).
