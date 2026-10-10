# ClaimGuard — 50% Scope (Topic 2)

**Title:** Span-Level Hallucination Detection for RAG  
**Delivery cut:** Objective 1 fully implemented; objectives 2–4 pending.

## Implemented (50%)

1. **Span-level detector** for RAG outputs  
   - **Inputs (custom, not hardcoded):**
     - `query` — user question (optional but recommended)
     - `source_text` — retrieved context / evidence
     - `generated_text` — model answer to check
   - **Outputs:** each sentence labeled `SUPPORTED` / `CONTRADICTED` / `BASELESS`
   - Overall hallucination rate + verdict
2. **UI:** blank form + paste / `.txt` upload + optional “Load sample”
3. **API:** `POST /api/verify` with `{ query, source_text, generated_text }`
4. History + dashboard KPIs

## Pending (remaining 50%)

2. Compare black-box methods (SelfCheckGPT, NLI, LLM-as-judge) vs fine-tuned detector  
3. Report span/response F1 on RAGTruth / HaluEval / FaithBench / HalluLens  
4. Optional abstain / regenerate mitigation + faithfulness gain

## How to use custom input

1. Open Verify Claims (fields start **empty**).
2. Paste your own query, context, and answer — or use **Load .txt** on each field.
3. Click **Detect hallucinations**.
4. Optional: **Load sample** only if you want the built-in demo texts.
