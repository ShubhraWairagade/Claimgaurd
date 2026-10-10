# ClaimGuard — Project Report

**Topic 2:** Span-Level Hallucination Detection for RAG  
**Student:** Raunak Rathi  
**Delivery scope:** ~50% (one core module)  
**Module implemented:** Span-level NLI hallucination detector  

---

## 1. Abstract

ClaimGuard verifies AI-generated text against a source document at sentence/span level, labeling each span SUPPORTED, CONTRADICTED, or BASELESS and producing an overall hallucination rate and verdict. This delivery implements the detector module plus a modern verification dashboard. Black-box baselines, RAGTruth fine-tuning, and mitigation are upcoming.

## 2. Problem Statement

Even with RAG, LLMs produce unsupported or contradictory spans. Reliable, cheap, span-level detectors — ideally without model internals — remain an active 2025–2026 problem. Public benchmarks such as RAGTruth show substantial headroom for better detectors.

## 3. Objectives (50% cut)

1. Build a span-level hallucination detector (query/source + generated answer → labeled spans).
2. Expose verification via FastAPI and a React dashboard with span highlighting.
3. Persist history and dashboard KPIs.
4. Document remaining Topic 2 goals as upcoming features.

**Deferred:** SelfCheckGPT / LLM-as-judge bake-off, RAGTruth fine-tune, abstain/regenerate mitigation.

## 4. System Design

```
source + generated → sentence split → evidence retrieval → NLI classify
    → span labels + hallucination rate + verdict → SQLite history
```

| Layer | Technology |
|-------|------------|
| Frontend | React, Vite, Tailwind |
| Backend | FastAPI, SQLite |
| Detector | DeBERTa-v3 MNLI/FEVER/ANLI + BGE (demo heuristic fallback) |

## 5. Implemented Module

**HallucinationDetector** (`backend/core.py`) finds the best source evidence per claim sentence, classifies with NLI (or demo heuristics), and aggregates an overall score. Demo mode enables demos without model downloads.

## 6. How to Run

```bash
cd claimguard/backend
DEMO_MODE=1 uvicorn main:app --reload --port 8002

cd claimguard/frontend
npm install && npm run dev
```

Use the sample texts preloaded in the Verify Claims screen.

## 7. Results Framing

This phase focuses on a working span detector and UI for qualitative analysis. Span-level F1 / AUROC on RAGTruth is upcoming.

## 8. Limitations

- Demo mode is lexical/heuristic, not trained NLI.
- No mitigation action after detection.
- No multi-detector comparison yet.

## 9. Future Work / Upcoming Features

See [UPCOMING_FEATURES.md](UPCOMING_FEATURES.md).

## 10. References

- Niu et al. RAGTruth. ACL 2024.
- Farquhar et al. Semantic Entropy. Nature 2024.
- Bang et al. HalluLens. ACL 2025.
