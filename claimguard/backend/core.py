"""
ClaimGuard — Core Module: Span-Level Hallucination Detector
Identifies unsupported, contradicted, and baseless spans in
AI-generated text against a source document.

Scope (50%): NLI-based span detector + overall verdict.
Set DEMO_MODE=1 to run without downloading DeBERTa / embedding models.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import List, Literal

HallucinationType = Literal["SUPPORTED", "CONTRADICTED", "BASELESS"]
DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"


@dataclass
class SpanResult:
    text: str
    label: HallucinationType
    confidence: float
    start: int
    end: int
    explanation: str


@dataclass
class VerificationResult:
    source_text: str
    generated_text: str
    spans: List[SpanResult]
    overall_score: float
    hallucination_rate: float
    verdict: str
    mode: str = "live"
    query: str = ""


def _demo_available() -> bool:
    return DEMO_MODE or os.getenv("FORCE_DEMO", "0") == "1"


class HallucinationDetector:
    """NLI-based span-level hallucination detector for RAG outputs.

    Input (Topic 2): query + retrieved context + generated answer
    Output: SUPPORTED / CONTRADICTED / BASELESS spans + verdict
    """

    def __init__(self, nli_model: str = "microsoft/deberta-v3-base-mnli-fever-anli"):
        self.demo = _demo_available()
        self.tokenizer = None
        self.model = None
        self.embedder = None
        self.label_map = {0: "CONTRADICTED", 1: "BASELESS", 2: "SUPPORTED"}

        if self.demo:
            return

        try:
            import torch
            from sentence_transformers import SentenceTransformer
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            self.tokenizer = AutoTokenizer.from_pretrained(nli_model)
            self.model = AutoModelForSequenceClassification.from_pretrained(nli_model)
            self.model.eval()
            if torch.cuda.is_available():
                self.model = self.model.cuda()
            self.embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")
        except Exception as exc:  # noqa: BLE001
            print(f"[ClaimGuard] Model load failed ({exc}); using demo detector.")
            self.demo = True

    def _split_sentences(self, text: str) -> List[dict]:
        sentences = []
        for match in re.finditer(r"[^.!?]+[.!?]+", text):
            sentences.append(
                {
                    "text": match.group().strip(),
                    "start": match.start(),
                    "end": match.end(),
                }
            )
        if not sentences and text.strip():
            sentences.append({"text": text.strip(), "start": 0, "end": len(text)})
        return sentences

    def _classify_span(self, premise: str, hypothesis: str) -> tuple:
        import torch

        inputs = self.tokenizer(
            premise[:1500],
            hypothesis,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        with torch.no_grad():
            logits = self.model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)[0]

        pred_idx = torch.argmax(probs).item()
        label = self.label_map[pred_idx]
        confidence = probs[pred_idx].item()
        return label, confidence

    def _find_best_evidence(self, claim: str, source_sentences: List[str]) -> tuple:
        if not source_sentences:
            return "", 0.0
        from sentence_transformers import util

        claim_emb = self.embedder.encode(claim, convert_to_tensor=True)
        src_embs = self.embedder.encode(source_sentences, convert_to_tensor=True)
        scores = util.cos_sim(claim_emb, src_embs)[0]
        best_idx = int(scores.argmax().item())
        return source_sentences[best_idx], float(scores[best_idx].item())

    def _demo_verify(
        self, source_text: str, generated_text: str, query: str = ""
    ) -> VerificationResult:
        gen_sentences = self._split_sentences(generated_text)
        src_sentences = [s["text"] for s in self._split_sentences(source_text)]
        src_tokens = set(re.findall(r"[a-z0-9]+", source_text.lower()))
        query_tokens = set(re.findall(r"[a-z0-9]+", query.lower())) if query else set()

        # Word-boundary polarity flips (stems + common inflections)
        negation_pairs = [
            ("increase", "decrease"),
            ("increased", "decreased"),
            ("increases", "decreases"),
            ("rise", "fall"),
            ("rose", "fell"),
            ("rising", "falling"),
            ("profit", "loss"),
            ("growth", "decline"),
            ("grew", "declined"),
            ("growing", "declining"),
            ("approved", "rejected"),
            ("higher", "lower"),
            ("gain", "loss"),
            ("up", "down"),
        ]

        spans: List[SpanResult] = []
        src_lower = source_text.lower()
        for sent in gen_sentences:
            claim_lower = sent["text"].lower()
            claim_tokens = set(re.findall(r"[a-z0-9]+", claim_lower))
            overlap = len(claim_tokens & src_tokens) / max(len(claim_tokens), 1)
            # Prefer evidence sentences that also overlap the user query
            if query_tokens and src_sentences:
                evidence = max(
                    src_sentences,
                    key=lambda s: len(
                        claim_tokens & set(re.findall(r"[a-z0-9]+", s.lower()))
                    )
                    + 0.5
                    * len(query_tokens & set(re.findall(r"[a-z0-9]+", s.lower()))),
                )
            else:
                evidence = max(
                    src_sentences or [""],
                    key=lambda s: len(
                        claim_tokens & set(re.findall(r"[a-z0-9]+", s.lower()))
                    ),
                )

            contradicted = False
            for a, b in negation_pairs:
                a_in_claim = bool(re.search(rf"\b{re.escape(a)}\b", claim_lower))
                b_in_claim = bool(re.search(rf"\b{re.escape(b)}\b", claim_lower))
                a_in_src = bool(re.search(rf"\b{re.escape(a)}\b", src_lower))
                b_in_src = bool(re.search(rf"\b{re.escape(b)}\b", src_lower))
                if (a_in_claim and b_in_src) or (b_in_claim and a_in_src):
                    contradicted = True
                    break

            # Source says "no/not/never X" but claim affirms X
            if not contradicted:
                for m in re.finditer(
                    r"\b(?:no|not|never|without)\s+([a-z]{4,})\b", src_lower
                ):
                    noun = m.group(1)
                    if re.search(rf"\b{re.escape(noun)}\b", claim_lower) and not re.search(
                        rf"\b(?:no|not|never|without)\s+{re.escape(noun)}\b",
                        claim_lower,
                    ):
                        contradicted = True
                        break

            stop = {
                "the", "a", "an", "of", "to", "and", "in", "on", "for", "was",
                "were", "is", "are", "during", "company", "completed", "three",
                "that", "this", "with", "from", "by", "as", "at", "or", "it",
            }
            novel = {
                t for t in claim_tokens - src_tokens if t not in stop and len(t) > 3
            }

            if contradicted:
                label: HallucinationType = "CONTRADICTED"
                confidence = 0.88
                explanation = "Demo detector: claim polarity conflicts with source wording."
            elif novel and overlap < 0.55:
                label = "BASELESS"
                confidence = 0.8
                explanation = (
                    "Demo detector: claim introduces details absent from the source."
                )
            elif overlap < 0.25:
                label = "BASELESS"
                confidence = 0.82
                explanation = "Demo detector: no matching content found in the source."
            elif overlap < 0.45:
                label = "BASELESS"
                confidence = 0.65
                explanation = "Demo detector: weak grounding; claim may be unsupported."
            else:
                label = "SUPPORTED"
                confidence = min(0.95, 0.55 + overlap)
                explanation = f'Supported by source: "{evidence[:100]}..."'
                if query:
                    explanation += f' (query: "{query[:60]}")'

            spans.append(
                SpanResult(
                    text=sent["text"],
                    label=label,
                    confidence=round(confidence, 3),
                    start=sent["start"],
                    end=sent["end"],
                    explanation=explanation,
                )
            )

        return self._finalize(source_text, generated_text, spans, mode="demo", query=query)

    def _finalize(
        self,
        source_text: str,
        generated_text: str,
        spans: List[SpanResult],
        mode: str,
        query: str = "",
    ) -> VerificationResult:
        supported = sum(1 for s in spans if s.label == "SUPPORTED")
        total = len(spans) if spans else 1
        hallucination_rate = round(1 - supported / total, 3)
        overall_score = round(supported / total, 3)

        if hallucination_rate == 0:
            verdict = "FULLY VERIFIED — All claims are supported by the source."
        elif hallucination_rate < 0.3:
            verdict = "MOSTLY VERIFIED — Minor unsupported claims detected."
        elif hallucination_rate < 0.6:
            verdict = "PARTIALLY VERIFIED — Significant unsupported content."
        else:
            verdict = "HIGH RISK — Majority of claims are not supported by the source."

        return VerificationResult(
            source_text=source_text,
            generated_text=generated_text,
            spans=spans,
            overall_score=overall_score,
            hallucination_rate=hallucination_rate,
            verdict=verdict,
            mode=mode,
            query=query or "",
        )

    def verify(
        self,
        source_text: str,
        generated_text: str,
        query: str = "",
    ) -> VerificationResult:
        """Verify generated RAG answer against retrieved context (and optional query)."""
        query = (query or "").strip()
        if self.demo:
            return self._demo_verify(source_text, generated_text, query=query)

        gen_sentences = self._split_sentences(generated_text)
        src_sentences = [s["text"] for s in self._split_sentences(source_text)]

        # Bias evidence search with the user query when provided
        evidence_pool = src_sentences
        if query and src_sentences and self.embedder is not None:
            from sentence_transformers import util

            q_emb = self.embedder.encode(query, convert_to_tensor=True)
            src_embs = self.embedder.encode(src_sentences, convert_to_tensor=True)
            scores = util.cos_sim(q_emb, src_embs)[0]
            order = scores.argsort(descending=True).tolist()
            evidence_pool = [src_sentences[i] for i in order]

        spans: List[SpanResult] = []
        for sent in gen_sentences:
            evidence, sim_score = self._find_best_evidence(sent["text"], evidence_pool)

            if sim_score < 0.3:
                label, confidence = "BASELESS", 0.85
                explanation = "No matching content found in the retrieved context."
            else:
                # NLI: does context entail the claim? Optionally condition with query.
                hypothesis = sent["text"]
                if query:
                    hypothesis = f"Regarding '{query}': {sent['text']}"
                label, confidence = self._classify_span(evidence, hypothesis)
                if label == "SUPPORTED":
                    explanation = f'Supported by context: "{evidence[:100]}..."'
                elif label == "CONTRADICTED":
                    explanation = f'Contradicts context: "{evidence[:100]}..."'
                else:
                    explanation = (
                        f'Not directly supported. Closest context: "{evidence[:80]}..."'
                    )
                if query:
                    explanation += f' | query="{query[:50]}"'

            spans.append(
                SpanResult(
                    text=sent["text"],
                    label=label,
                    confidence=round(float(confidence), 3),
                    start=sent["start"],
                    end=sent["end"],
                    explanation=explanation,
                )
            )

        return self._finalize(
            source_text, generated_text, spans, mode="live", query=query
        )