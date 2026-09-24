from compliance.agents import verifier
from compliance.agents.context import label_passages
from compliance.agents.documents import matched_triggers, required_documents
from compliance.agents.orchestrator import Advisor, detect_jurisdictions
from compliance.corpus.lookup import CorpusLookup
from compliance.llm import NoLLM
from compliance.models import Claim, ScoredPassage
from compliance.retrieval.bm25 import BM25Index
from compliance.retrieval.hybrid import Retriever, rrf


def test_bm25_ranks_and_filters_by_jurisdiction(passages):
    index = BM25Index(passages)
    hits = index.search("probation period months", k=3)
    assert hits[0][0].article == "9"
    only_eu = index.search("probation period", jurisdictions={"EU"})
    assert all(p.jurisdiction == "EU" for p, _ in only_eu)


def test_rrf_prefers_items_ranked_high_in_both_lists():
    fused = rrf([["a", "b", "c"], ["b", "a", "d"]])
    assert max(fused, key=fused.get) in {"a", "b"}
    assert fused["d"] < fused["a"]


def test_verifier_accepts_verbatim_quotes_only(passages):
    sps = label_passages([ScoredPassage(passage=p, score=1.0) for p in passages])
    by_label = {sp.label: sp for sp in sps}
    good = Claim(text="Probation is capped.", passage="P3", quote="probationary period not exceeding (6) six months")
    bad_quote = Claim(text="Probation is capped.", passage="P3", quote="probation may last up to one year")
    bad_label = Claim(text="x", passage="P42", quote="probationary period not exceeding (6) six months")
    short = Claim(text="x", passage="P3", quote="six months")
    assert verifier.check(good, by_label).status == "verified"
    assert verifier.check(good, by_label).article == "9"
    assert verifier.check(bad_quote, by_label).reason == "quote not found in the cited passage"
    assert verifier.check(bad_label, by_label).status == "rejected"
    assert verifier.check(short, by_label).status == "rejected"


def test_detect_jurisdictions():
    assert detect_jurisdictions("Hiring in Dubai with AI") == ["AE"]
    assert detect_jurisdictions("GDPR and Saudi PDPL transfer") == ["SA", "EU"]
    assert detect_jurisdictions("Can we do this in Dubai?") == ["AE"]
    assert detect_jurisdictions("generic question") == ["AE", "SA", "EU"]


def test_document_rules_follow_triggers_and_check_basis(passages):
    assert {"recruitment", "ai_system"} <= matched_triggers("AI screening of CVs")
    docs = required_documents("AI screening of CVs for hiring", ["AE"], CorpusLookup(passages))
    by_id = {d.id: d for d in docs}
    assert by_id["ae_employment_contract"].basis[0]["check"] == "confirmed"
    assert by_id["ae_lawful_basis_record"].basis[0]["check"] == "source_missing"
    assert all(d.id.startswith("ae_") for d in docs)


def _advisor(passages, llm):
    return Advisor(Retriever(passages, use_vector=False), CorpusLookup(passages), llm)


def test_extractive_mode_without_llm(passages):
    a = _advisor(passages, NoLLM()).ask("What is the maximum probationary period?", ["AE"])
    assert a.mode == "extractive" and a.status == "partial"
    assert a.passages and not a.findings
    assert a.review_required


def test_abstains_without_matching_provisions(passages):
    a = _advisor(passages, NoLLM()).ask("zebra migration statistics", ["AE"])
    assert a.status == "insufficient_basis" and not a.passages


def test_generated_answer_drops_fabricated_quotes_and_keeps_disputes(passages, fake_llm_factory):
    analyst = {
        "findings": [
            {"text": "Probation may not exceed six months.", "passage": "P1",
             "quote": "probationary period not exceeding (6) six months"},
            {"text": "Probation can be extended to a year.", "passage": "P1",
             "quote": "the probation may be extended to one year"},
            {"text": "A written contract in two copies is required.", "passage": "P2",
             "quote": "The contract shall be made in two copies"},
        ],
        "open_questions": ["Is the worker in a free zone?"],
    }
    challenger = {
        "disputed": [{"index": 2, "reason": "Passage is about copies, not about whether writing is required."}],
        "counterpoints": [
            {"text": "Discrimination rules also apply to AI screening.", "passage": "P3",
             "quote": "national or social origin or disability which impairs equality"},
            {"text": "Invented exception.", "passage": "P2", "quote": "unless the employer uses an AI system"},
        ],
        "open_questions": ["is the worker in a free zone?"],
    }
    a = _advisor(passages, fake_llm_factory(analyst, challenger)).ask(
        "probationary period and contract copies discrimination", ["AE"]
    )
    by_label = {sp.label: sp.passage.article for sp in a.passages}
    assert by_label["P1"] == "9"  # sanity check on retrieval order used by the fake responses

    assert [c.text for c in a.findings] == ["Probation may not exceed six months."]
    assert {c.status for c in a.counterpoints} == {"verified", "disputed"}
    assert len(a.rejected) == 2  # fabricated finding + fabricated counterpoint
    assert a.status == "partial"
    assert a.citation_coverage == round(3 / 5, 3)
    assert a.open_questions == ["Is the worker in a free zone?"]  # deduplicated
