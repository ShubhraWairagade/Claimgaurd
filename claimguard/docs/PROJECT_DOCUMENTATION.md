# ClaimGuard — Project Documentation

**Product:** Span-level hallucination detection for RAG outputs  
**Folder:** `claimguard/`  
**Topic alignment:** Topic 2 — Span-Level Hallucination Detection (50% = Objective 1)

---

## 1. What this project does

ClaimGuard checks whether a **generated RAG answer** is faithful to **retrieved context**, optionally guided by the user **query**. Each sentence (span) is labeled:

- **SUPPORTED** — entailed by context  
- **CONTRADICTED** — conflicts with context  
- **BASELESS** — not grounded in context  

It returns a hallucination rate and overall verdict.

## 2. Who it is for

Compliance, finance reporting, and RAG product teams validating groundedness before publishing AI text.

## 3. Architecture

```
Browser (React, port 5172)
    → /api/* 
FastAPI (port 8002)
    → core.HallucinationDetector
    → SQLite (verifications)
```

| Layer | Path | Role |
|-------|------|------|
| UI | `frontend/src/App.jsx` | Login, dashboard, verify (custom inputs), history, upcoming |
| API helper | `frontend/src/api.js` | Production API base URL |
| API | `backend/main.py` | `/api/verify`, history, stats |
| Core | `backend/core.py` | Sentence split, evidence match, NLI/heuristic labels |
| Samples | `samples/` | Optional demo texts (UI starts empty) |

## 4. User flow

1. Login.  
2. **Dashboard** — KPIs only.  
3. **Verify Claims** — fields start **empty** (not hardcoded):
   - Query (optional)
   - Retrieved context
   - Generated answer  
   Paste, **Load .txt**, or optional **Load sample**.  
4. Review color-coded spans + verdict.  
5. History / Upcoming.

## 5. API contract

```http
POST /api/verify
Content-Type: application/json

{
  "query": "What was Q3 revenue growth?",
  "source_text": "Revenue grew 12% year-over-year...",
  "generated_text": "Revenue declined 12% year-over-year..."
}
```

## 6. Models

| Mode | Detector |
|------|----------|
| `DEMO_MODE=1` | Lexical / polarity / negation heuristics on **your** text |
| `DEMO_MODE=0` | DeBERTa-v3 MNLI/FEVER/ANLI + BGE evidence retrieval |

**No generative LLM** is required for ClaimGuard.

## 7. 50% vs remaining Topic 2

| Goal | Status |
|------|--------|
| 1. Span-level detector (query + context + answer) | **Done** |
| 2. Black-box vs fine-tuned comparison | Pending |
| 3. F1 on RAGTruth / HaluEval / etc. | Pending |
| 4. Abstain / regenerate mitigation | Pending |

See `docs/SCOPE_50.md`.

## 8. Local run

```bash
cd claimguard/backend
pip install -r requirements.txt
DEMO_MODE=1 uvicorn main:app --reload --port 8002

cd ../frontend
npm install && npm run dev
# http://127.0.0.1:5172
```

## 9. Tests

```bash
cd claimguard/backend
DEMO_MODE=1 pytest tests -q
```

## 10. Related docs

| File | Purpose |
|------|---------|
| `README.md` | Quick start |
| `docs/PROJECT_DOCUMENTATION.md` | This file |
| `docs/SCOPE_50.md` | Scope cut |
| `docs/REPORT.md` | Report |
| `docs/UPCOMING_FEATURES.md` | Remaining goals |
| `docs/PRESENTATION.pptx` | Slides |
