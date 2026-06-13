"""Smoke tests for the HTTP API using FastAPI's TestClient.

The app is configured via env vars to use the offline fake providers and a
temporary database, so these run with no external services.
"""

import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_DB_PATH", str(tmp_path / "api.db"))
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.setenv("EMBED_PROVIDER", "fake")
    # Import after env is set so module-level settings pick up the overrides.
    import importlib

    import app.main as main

    importlib.reload(main)
    return TestClient(main.app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["llm_provider"] == "FakeChat"


def test_ingest_and_chat_flow(client):
    resp = client.post(
        "/ingest",
        json={"source": "kb.txt", "text": "The sky appears blue due to Rayleigh scattering."},
    )
    assert resp.status_code == 200
    assert resp.json()["chunks"] >= 1

    docs = client.get("/documents").json()["documents"]
    assert len(docs) == 1

    resp = client.post("/chat", json={"question": "why is the sky blue?"})
    assert resp.status_code == 200
    frames = [json.loads(line) for line in resp.text.splitlines() if line]
    types = [f["type"] for f in frames]
    assert types[0] == "citations"
    assert "token" in types
    assert types[-1] == "done"


def test_chat_rejects_empty_question(client):
    resp = client.post("/chat", json={"question": "   "})
    assert resp.status_code == 400


def test_ingest_rejects_empty_text(client):
    resp = client.post("/ingest", json={"source": "x", "text": "  "})
    assert resp.status_code == 400
