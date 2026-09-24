import pytest

from compliance.cases.excel_store import CaseError, CaseStore
from compliance.corpus.registry import load_registry
from compliance.education.content import Catalog, curriculum, iter_citations, scenarios
from compliance.education.progress import ProgressError, ProgressStore


@pytest.fixture
def store(tmp_path):
    return CaseStore(tmp_path / "cases" / "cases.xlsx")


def test_case_lifecycle_and_document_alerts(store):
    answer = {
        "status": "partial",
        "findings": [{"source_id": "uae_labour_law", "article": "8"}],
        "documents": [
            {"id": "ae_employment_contract", "name": "Contract", "mandatory": True, "why": "w", "basis": []},
            {"id": "ae_dpia", "name": "DPIA", "mandatory": False, "why": "w", "basis": []},
        ],
    }
    cid = store.create_case("Layla", "Can we screen CVs with AI?", ["AE"], "HR", "CV ranking", answer=answer)
    case = store.get_case(cid)
    assert case["related_provisions"] == "uae_labour_law art. 8"
    assert [d["doc_id"] for d in case["documents"]] == ["ae_employment_contract", "ae_dpia"]
    assert case["alerts"] == ["Mandatory document missing: Contract"]
    assert store.list_cases()[0]["missing_mandatory"] == 1

    store.update_document(cid, "ae_employment_contract", actor="Layla", status="received")
    assert store.get_case(cid)["alerts"] == []

    doc_id = store.add_document(cid, "Vendor contract", True, "2000-01-01", actor="Layla")
    assert any("Overdue" in a for a in store.get_case(cid)["alerts"])
    assert doc_id == "doc-3"


def test_approval_requires_human_reviewer(store):
    cid = store.create_case("Omar", "Question?", ["SA"])
    with pytest.raises(CaseError):
        store.update_case(cid, "Omar", status="approved")
    case = store.update_case(cid, "Omar", status="approved", reviewer="Counsel A")
    assert case["status"] == "approved" and case["log"][-1]["action"] == "updated"


def test_upload_names_are_sanitised(store):
    cid = store.create_case("Omar", "Question?", ["AE"])
    doc_id = store.add_document(cid, "Policy", False)
    rel = store.save_upload(cid, doc_id, "../../evil name?.pdf", b"%PDF-1.4")
    assert rel.startswith(f"{cid}/") and ".." not in rel
    assert (store.files_dir / rel).read_bytes() == b"%PDF-1.4"
    with pytest.raises(CaseError):
        store.get_case("../../etc")


def test_content_is_consistent():
    registry = load_registry()
    source_ids = {s.id for s in registry.sources}
    for where, cite in iter_citations():
        assert cite["source"] in source_ids, where
        assert cite.get("expect"), f"{where}: every citation needs expected wording"
    module_ids = [m["id"] for m in curriculum()["modules"]]
    assert len(module_ids) == len(set(module_ids))
    for m in curriculum()["modules"]:
        assert set(m.get("prerequisites", [])) <= set(module_ids)
        for q in m.get("quiz", []):
            assert 0 <= q["answer"] < len(q["options"]["en"]), q["id"]
    for t in curriculum()["tracks"]:
        assert set(t["modules"]) <= set(module_ids)
    for s in scenarios()["scenarios"]:
        assert set(s["jurisdictions"]) <= set(registry.jurisdictions)


def test_catalog_hides_answers_and_grades(tmp_path):
    catalog = Catalog({})
    module = catalog.module("uae-labour", "ar")
    assert module["title"] != "UAE Labour Law touchpoints for AI in HR"  # Arabic title used
    assert "answer" not in module["quiz"][0]
    graded = catalog.grade("uae-labour-q1", 1, "en")
    assert graded["correct"] and graded["cite"]["check"] == "unchecked"
    assert catalog.grade("missing", 0, "en") is None


def test_progress_scoring(tmp_path):
    progress = ProgressStore(tmp_path / "p.db")
    progress.ensure_learner("amal", "Amal", "ar")
    quiz = ["q1", "q2", "q3"]
    progress.record_attempt("amal", "m", "q1", 0, False)
    progress.record_attempt("amal", "m", "q1", 1, True)  # latest attempt counts
    progress.record_attempt("amal", "m", "q2", 1, True)
    assert progress.module_status("amal", "m", quiz)["completed"] is False
    progress.record_attempt("amal", "m", "q3", 1, True)
    status = progress.module_status("amal", "m", quiz)
    assert status == {"answered": 3, "total": 3, "score": 1.0, "completed": True}
    with pytest.raises(ProgressError):
        progress.ensure_learner("bad id!")
