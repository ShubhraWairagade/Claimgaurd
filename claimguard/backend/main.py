"""ClaimGuard — FastAPI Backend

50% Topic 2 scope: span-level hallucination detector for RAG outputs.
Input: query + retrieved context + generated answer
Output: SUPPORTED / CONTRADICTED / BASELESS spans
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="ClaimGuard", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB = "database/claimguard.db"


def init_db():
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS verifications (
            id TEXT PRIMARY KEY,
            query_preview TEXT DEFAULT '',
            source_preview TEXT,
            generated_preview TEXT,
            overall_score REAL,
            hallucination_rate REAL,
            verdict TEXT,
            span_count INTEGER,
            flagged_count INTEGER,
            spans TEXT,
            created_at TEXT
        );
        """
    )
    # Migrate older DBs that lack query_preview
    cols = {r[1] for r in conn.execute("PRAGMA table_info(verifications)").fetchall()}
    if "query_preview" not in cols:
        try:
            conn.execute(
                "ALTER TABLE verifications ADD COLUMN query_preview TEXT DEFAULT ''"
            )
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()


init_db()

detector = None


def get_detector():
    global detector
    if detector is None:
        from core import HallucinationDetector

        detector = HallucinationDetector()
    return detector


class VerifyRequest(BaseModel):
    """Custom RAG hallucination check — all fields are user-supplied."""

    query: Optional[str] = Field(
        default="",
        description="User question that produced the RAG answer (optional but recommended)",
    )
    source_text: str = Field(
        ...,
        description="Retrieved context / source evidence grounding the answer",
    )
    generated_text: str = Field(
        ...,
        description="Model-generated answer to verify span-by-span",
    )


class SpanResponse(BaseModel):
    text: str
    label: str
    confidence: float
    start: int
    end: int
    explanation: str


class VerifyResponse(BaseModel):
    id: str
    query: str = ""
    overall_score: float
    hallucination_rate: float
    verdict: str
    spans: List[SpanResponse]
    total_spans: int
    flagged_spans: int
    mode: str = "live"


@app.post("/api/verify", response_model=VerifyResponse)
async def verify_text(req: VerifyRequest):
    if len(req.source_text.strip()) < 10:
        raise HTTPException(400, "Retrieved context is too short (min 10 characters).")
    if len(req.generated_text.strip()) < 10:
        raise HTTPException(400, "Generated answer is too short (min 10 characters).")

    det = get_detector()
    result = det.verify(
        source_text=req.source_text,
        generated_text=req.generated_text,
        query=req.query or "",
    )

    vid = str(uuid.uuid4())[:8]
    spans_data = [
        {
            "text": s.text,
            "label": s.label,
            "confidence": s.confidence,
            "start": s.start,
            "end": s.end,
            "explanation": s.explanation,
        }
        for s in result.spans
    ]
    flagged = sum(1 for s in result.spans if s.label != "SUPPORTED")

    conn = sqlite3.connect(DB)
    # Support both new schema (11 cols) and legacy (10 cols)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(verifications)").fetchall()}
    if "query_preview" in cols:
        conn.execute(
            "INSERT INTO verifications (id, query_preview, source_preview, generated_preview, overall_score, hallucination_rate, verdict, span_count, flagged_count, spans, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                vid,
                (req.query or "")[:200],
                req.source_text[:200],
                req.generated_text[:200],
                result.overall_score,
                result.hallucination_rate,
                result.verdict,
                len(result.spans),
                flagged,
                json.dumps(spans_data),
                datetime.now().isoformat(),
            ),
        )
    else:
        conn.execute(
            "INSERT INTO verifications VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                vid,
                req.source_text[:200],
                req.generated_text[:200],
                result.overall_score,
                result.hallucination_rate,
                result.verdict,
                len(result.spans),
                flagged,
                json.dumps(spans_data),
                datetime.now().isoformat(),
            ),
        )
    conn.commit()
    conn.close()

    return VerifyResponse(
        id=vid,
        query=req.query or "",
        overall_score=result.overall_score,
        hallucination_rate=result.hallucination_rate,
        verdict=result.verdict,
        spans=spans_data,
        total_spans=len(result.spans),
        flagged_spans=flagged,
        mode=getattr(result, "mode", "demo" if det.demo else "live"),
    )


@app.get("/api/history")
async def get_history():
    conn = sqlite3.connect(DB)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(verifications)").fetchall()}
    if "query_preview" in cols:
        rows = conn.execute(
            "SELECT id, query_preview, source_preview, generated_preview, overall_score, hallucination_rate, verdict, span_count, flagged_count, created_at FROM verifications ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
        conn.close()
        return [
            {
                "id": r[0],
                "query_preview": r[1] or "",
                "source_preview": r[2],
                "generated_preview": r[3],
                "overall_score": r[4],
                "hallucination_rate": r[5],
                "verdict": r[6],
                "span_count": r[7],
                "flagged_count": r[8],
                "created_at": r[9],
            }
            for r in rows
        ]
    rows = conn.execute(
        "SELECT id, source_preview, generated_preview, overall_score, hallucination_rate, verdict, span_count, flagged_count, created_at FROM verifications ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "query_preview": "",
            "source_preview": r[1],
            "generated_preview": r[2],
            "overall_score": r[3],
            "hallucination_rate": r[4],
            "verdict": r[5],
            "span_count": r[6],
            "flagged_count": r[7],
            "created_at": r[8],
        }
        for r in rows
    ]


@app.get("/api/verification/{vid}")
async def get_verification(vid: str):
    conn = sqlite3.connect(DB)
    row = conn.execute(
        "SELECT * FROM verifications WHERE id=?",
        (vid,),
    ).fetchone()
    cols = [r[1] for r in conn.execute("PRAGMA table_info(verifications)").fetchall()]
    conn.close()
    if not row:
        raise HTTPException(404, "Verification not found")
    data = dict(zip(cols, row))
    return {
        "id": data["id"],
        "query_preview": data.get("query_preview", ""),
        "source_preview": data.get("source_preview"),
        "generated_preview": data.get("generated_preview"),
        "overall_score": data.get("overall_score"),
        "hallucination_rate": data.get("hallucination_rate"),
        "verdict": data.get("verdict"),
        "spans": json.loads(data.get("spans") or "[]"),
        "created_at": data.get("created_at"),
    }


@app.get("/api/stats")
async def get_stats():
    conn = sqlite3.connect(DB)
    total = conn.execute("SELECT COUNT(*) FROM verifications").fetchone()[0]
    avg_rate = conn.execute(
        "SELECT AVG(hallucination_rate) FROM verifications"
    ).fetchone()[0]
    avg_score = conn.execute(
        "SELECT AVG(overall_score) FROM verifications"
    ).fetchone()[0]
    flagged = conn.execute(
        "SELECT SUM(flagged_count) FROM verifications"
    ).fetchone()[0]
    recent = conn.execute(
        "SELECT id, verdict, hallucination_rate, flagged_count, created_at FROM verifications ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    conn.close()

    return {
        "verifications": total,
        "avg_hallucination_rate": round(avg_rate or 0, 3),
        "avg_overall_score": round(avg_score or 0, 3),
        "flagged_spans_total": flagged or 0,
        "model_loaded": detector is not None,
        "demo_mode": bool(getattr(detector, "demo", True))
        if detector
        else os.getenv("DEMO_MODE", "0") == "1",
        "recent": [
            {
                "id": r[0],
                "verdict": r[1],
                "hallucination_rate": r[2],
                "flagged_count": r[3],
                "created_at": r[4],
            }
            for r in recent
        ],
    }


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "detector_loaded": detector is not None,
        "demo_mode": os.getenv("DEMO_MODE", "0") == "1",
        "module": "span-level-nli-hallucination-detector",
        "scope": "50%",
        "inputs": ["query", "retrieved_context", "generated_answer"],
        "outputs": ["SUPPORTED", "CONTRADICTED", "BASELESS"],
        "pending": [
            "black-box baselines comparison",
            "RAGTruth fine-tune + F1",
            "abstain/regenerate mitigation",
        ],
    }
