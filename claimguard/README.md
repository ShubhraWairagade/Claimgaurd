# ClaimGuard — Span-Level Hallucination Detection for RAG

**Topic 2 · 50% scope**  
**Implemented:** Objective 1 — span-level detector (`SUPPORTED` / `CONTRADICTED` / `BASELESS`) on **custom** query + context + answer.

**Pending (remaining 50%):** black-box baselines comparison, RAGTruth fine-tune + F1, abstain/regenerate — see [`docs/UPCOMING_FEATURES.md`](docs/UPCOMING_FEATURES.md) and [`docs/SCOPE_50.md`](docs/SCOPE_50.md).

## Quick Start

```bash
# Backend (demo mode — no GPU/models required)
cd backend
pip install -r requirements.txt
DEMO_MODE=1 uvicorn main:app --reload --port 8002

# Frontend
cd frontend
npm install && npm run dev
# → http://localhost:5172
```

## Custom input (default)

The Verify screen starts **empty** (nothing hardcoded). Provide:

1. **Query** — user question (optional but recommended)
2. **Retrieved context** — source evidence / RAG passages
3. **Generated answer** — model output to check

Paste text, or use **Load .txt** on each field. **Load sample** is optional for demos only.

### API

```bash
curl -s -X POST http://127.0.0.1:8002/api/verify \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "What was Q3 revenue growth?",
    "source_text": "Revenue grew 12% year-over-year to $4.2 billion.",
    "generated_text": "Revenue declined 12% year-over-year to $4.2 billion."
  }'
```

Optional samples: [`samples/`](samples/) (`verification_pair.json`, `source_report.txt`, `generated_summary.txt`).

### Login

- Email: `demo@college.edu` / Password: `demo123` (or any non-empty pair)

## Tests

```bash
cd backend && DEMO_MODE=1 pytest tests -q
```

## Stack
- **Backend:** FastAPI + SQLite
- **AI:** DeBERTa-v3 MNLI/FEVER/ANLI + BGE (or demo heuristics) — **not** a generative LLM
- **Frontend:** React + Vite + Tailwind

## Docs
- [`docs/PROJECT_DOCUMENTATION.md`](docs/PROJECT_DOCUMENTATION.md) — full project explanation
- [`docs/SCOPE_50.md`](docs/SCOPE_50.md) — implemented vs pending for Topic 2
- [`docs/REPORT.md`](docs/REPORT.md)
- [`docs/PRESENTATION.pptx`](docs/PRESENTATION.pptx)
- [`docs/UPCOMING_FEATURES.md`](docs/UPCOMING_FEATURES.md)
- Root: [`../CODE_WALKTHROUGH.md`](../CODE_WALKTHROUGH.md) · [`../DEPLOYMENT_VERCEL.md`](../DEPLOYMENT_VERCEL.md)

Dashboard is status-only; paste/verify lives on **Verify Claims**.

### Demo steps

1. Open http://localhost:5172 → sign in → **Dashboard** → **Open Verifier**.
2. Paste `samples/source_report.txt` into **Source evidence** (or edit the preloaded sample).
3. Paste `samples/generated_summary.txt` into **Generated / RAG output**.
4. Click **Detect hallucinations** — spans are graded against **your pasted text**, not fixed canned-only responses.

`DEMO_MODE=1` uses lightweight lexical/polarity heuristics, still on the exact texts you submit.

**Models:** No generative LLM. Classifier = DeBERTa NLI (live) or heuristics (demo).  
**Status:** [`../IMPLEMENTATION_STATUS.md`](../IMPLEMENTATION_STATUS.md)

## Tests

```bash
cd backend && DEMO_MODE=1 pytest tests -q
```

API check:

```bash
curl -s -X POST http://127.0.0.1:8002/api/verify \
  -H 'Content-Type: application/json' \
  -d @samples/verification_pair.json
```

## Stack
- **Backend:** FastAPI + SQLite
- **AI:** DeBERTa-v3 MNLI/FEVER/ANLI + BGE (auto demo fallback)
- **Frontend:** React + Vite + Tailwind

## Docs
- [`docs/REPORT.md`](docs/REPORT.md) — project report
- [`docs/PRESENTATION.pptx`](docs/PRESENTATION.pptx) — slides
- [`docs/UPCOMING_FEATURES.md`](docs/UPCOMING_FEATURES.md) — future work

## API
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/verify` | Span-level verification |
| GET | `/api/history` | Past verifications |
| GET | `/api/stats` | Dashboard KPIs |
| GET | `/api/health` | Health |
