"""ClaimGuard API tests — isolated module load."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["DEMO_MODE"] = "1"
os.environ["FORCE_DEMO"] = "1"

BACKEND = Path(__file__).resolve().parents[1]
SAMPLES = BACKEND.parent / "samples"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def client(tmp_path, monkeypatch):
    for key in ("main", "core"):
        sys.modules.pop(key, None)
    monkeypatch.chdir(BACKEND)
    sys.path.insert(0, str(BACKEND))
    core = _load("core", BACKEND / "core.py")
    sys.modules["core"] = core
    appmod = _load("claimguard_main_test", BACKEND / "main.py")
    db = tmp_path / "test.db"
    monkeypatch.setattr(appmod, "DB", str(db))
    appmod.init_db()
    appmod.detector = None
    with TestClient(appmod.app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_verify_detects_planted_errors(client):
    pair = json.loads((SAMPLES / "verification_pair.json").read_text())
    payload = {
        "query": "What were the Q3 highlights?",
        "source_text": pair["source_text"],
        "generated_text": pair["generated_text"],
    }
    r = client.post("/api/verify", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["total_spans"] >= 1
    assert data["hallucination_rate"] > 0
    assert data.get("query") == payload["query"]
    labels = {s["label"] for s in data["spans"]}
    assert labels & {"CONTRADICTED", "BASELESS"}


def test_verify_uses_user_text_not_fixed_demo(client):
    source = (
        "Alpha Corp reported revenue of exactly nine million dollars in May. "
        "No acquisitions were completed during the quarter."
    )
    generated = (
        "Alpha Corp reported revenue of exactly nine million dollars in May. "
        "The company completed three acquisitions during the quarter."
    )
    r = client.post(
        "/api/verify",
        json={
            "query": "Did Alpha Corp complete acquisitions?",
            "source_text": source,
            "generated_text": generated,
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["flagged_spans"] >= 1
    joined = " ".join(s["text"].lower() for s in data["spans"] if s["label"] != "SUPPORTED")
    assert "acquisition" in joined


def test_custom_short_inputs_accepted(client):
    r = client.post(
        "/api/verify",
        json={
            "query": "Who won?",
            "source_text": "Team Blue won the championship in 2024 after a close final.",
            "generated_text": "Team Red won the championship in 2024 after a close final.",
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["total_spans"] >= 1
    assert data["query"] == "Who won?"


def test_history(client):
    pair = json.loads((SAMPLES / "verification_pair.json").read_text())
    assert (
        client.post(
            "/api/verify",
            json={
                "query": "Q3 summary?",
                "source_text": pair["source_text"],
                "generated_text": pair["generated_text"],
            },
        ).status_code
        == 200
    )
    hist = client.get("/api/history").json()
    assert len(hist) >= 1
