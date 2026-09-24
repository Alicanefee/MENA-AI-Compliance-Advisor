import pytest
from fastapi.testclient import TestClient

from compliance.api.main import create_app
from compliance.cases.excel_store import CaseStore
from compliance.education.progress import ProgressStore
from compliance.llm import NoLLM


@pytest.fixture
def client(passages, tmp_path):
    app = create_app(
        passages=passages,
        llm=NoLLM(),
        cases=CaseStore(tmp_path / "cases" / "cases.xlsx"),
        progress=ProgressStore(tmp_path / "progress.db"),
    )
    return TestClient(app)


def test_health_and_ui(client):
    health = client.get("/api/health").json()
    assert health["mode"] == "extractive" and health["passages"] == 6
    assert client.get("/").status_code == 200
    assert client.get("/static/app.js").status_code == 200
    assert "not legal advice" in client.get("/api/disclaimer").json()["full"]


def test_ask_returns_sources_and_documents(client):
    r = client.post("/api/ask", json={"question": "Using software to filter job applications and evaluate candidates", "jurisdictions": ["EU"]})
    body = r.json()
    assert r.status_code == 200
    assert body["passages"][0]["passage"]["article"] == "Annex III"
    assert any(d["id"] == "eu_high_risk_classification" for d in body["documents"])
    assert client.post("/api/ask", json={"question": "x"}).status_code == 422


def test_case_flow(client):
    r = client.post("/api/cases", json={"owner": "Layla", "question": "Can we use AI to screen CVs in Dubai?"})
    assert r.status_code == 200
    created = r.json()
    cid = created["case_id"]
    assert created["recommended_modules"][0]["id"] == "foundations"
    case = client.get(f"/api/cases/{cid}").json()
    assert case["jurisdictions"] == "AE" and case["documents"]
    assert "legal responsibility rests with the user" in case["disclaimer"]
    assert "disclaimer" in created

    doc_id = case["documents"][0]["doc_id"]
    up = client.post(f"/api/cases/{cid}/documents/{doc_id}/upload", files={"file": ("contract.pdf", b"%PDF-1.4", "application/pdf")})
    assert up.status_code == 200 and up.json()["case"]["documents"][0]["status"] == "received"
    bad = client.post(f"/api/cases/{cid}/documents/{doc_id}/upload", files={"file": ("run.exe", b"MZ", "application/octet-stream")})
    assert bad.status_code == 400

    assert client.patch(f"/api/cases/{cid}", json={"actor": "Layla", "status": "approved"}).status_code == 400
    ok = client.patch(f"/api/cases/{cid}", json={"actor": "Layla", "status": "approved", "reviewer": "Counsel"})
    assert ok.json()["status"] == "approved"
    assert client.get("/api/cases/CASE-00000000").status_code == 404


def test_learning_flow(client):
    modules = client.get("/api/learn/modules", params={"learner_id": "amal"}).json()
    assert modules["modules"][0]["progress"]["answered"] == 0
    detail = client.get("/api/learn/modules/uae-labour").json()
    point = detail["lessons"][0]["points"][0]
    assert point["cite"]["check"] == "confirmed"  # matched against the fixture passage
    r = client.post("/api/learn/answer", json={"learner_id": "amal", "quiz_id": "uae-labour-q1", "answer": 1}).json()
    assert r["correct"] and r["module_progress"]["answered"] == 1 and r["disclaimer"]
    assert client.post("/api/learn/answer", json={"learner_id": "bad id", "quiz_id": "uae-labour-q1", "answer": 1}).status_code == 400

    scen = client.get("/api/learn/scenarios").json()
    answer = client.get(f"/api/learn/scenarios/{scen[0]['id']}/q1/answer").json()
    assert answer["points"] and answer["could_change"]


def test_sources_listing(client):
    sources = client.get("/api/sources").json()
    by_id = {s["id"]: s for s in sources}
    assert by_id["uae_labour_law"]["extraction"] == "ai"
    assert by_id["uae_pdpl"]["passages"] == 0
    assert client.get("/api/sources/unknown/diffs").status_code == 404
