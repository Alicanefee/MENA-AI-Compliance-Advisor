from compliance.corpus.ai_extract import AIArticle, parse_blocks, score_against_text_layer
from compliance.corpus.chunker import chunk_text
from compliance.corpus.extract import apply_trim, clean_text
from compliance.corpus.lookup import CorpusLookup
from compliance.corpus.registry import Trim, load_registry
from compliance.corpus.updates import diff_texts


def src(source_id="sa_labour_law"):
    return load_registry().get(source_id)


def test_registry_sources_are_unique_and_complete():
    registry = load_registry()
    ids = [s.id for s in registry.sources]
    assert len(ids) == len(set(ids))
    for s in registry.sources:
        assert s.jurisdiction in registry.jurisdictions
        assert s.urls or s.manual_url


def test_chunker_plain_headings_and_toc_dedup():
    text = (
        "Contents\nArticle 1\nArticle 2\n"  # table of contents: bodies too short, dropped
        "Article 1\nDefinitions\nIn this law the following words have the meanings shown against each of them.\n"
        "Article 2\nThe employment contract shall be executed in duplicate, one copy for each party to keep.\n"
    )
    passages = chunk_text(text, src())
    assert [p.article for p in passages] == ["1", "2"]
    assert passages[0].heading == "Definitions"
    assert passages[1].heading == ""  # first line is a sentence, not a title
    assert "duplicate" in passages[1].text


def test_chunker_parenthesised_annex_and_arabic():
    text = (
        "Article (8)\nEmployment Contract\nThe contract shall be made in two copies for both parties.\n"
        "ANNEX III\nHigh-risk AI systems referred to in Article 6(2) are listed in this annex.\n"
        "المادة (12)\nيجب أن يكون عقد العمل مكتوباً ومحرراً من نسختين لكل طرف.\n"
    )
    labels = [p.article for p in chunk_text(text, src())]
    assert labels == ["8", "Annex III", "12"]


def test_chunker_without_headings_uses_sections():
    passages = chunk_text("Principle one: fairness applies throughout the lifecycle of the system.", src("sa_ai_ethics"))
    assert passages[0].article == "§1"


def test_clean_text_fixes_glyph_names_and_page_numbers():
    assert clean_text("/T_he worker\n12\nshall ﬁle") == "The worker\nshall file"


def test_trim_cuts_at_nth_occurrence():
    text = "Title Cabinet Resolution No. (1) body Cabinet Resolution No. (1) appended"
    assert apply_trim(text, Trim(end_marker="cabinet resolution no. (1)", occurrence=2)) == "Title Cabinet Resolution No. (1) body"


def test_lookup_statuses(passages):
    lookup = CorpusLookup(passages)
    assert lookup.check("uae_labour_law", "9", ["six months"]) == "confirmed"
    assert lookup.check("uae_labour_law", "9", ["twelve months"]) == "not_confirmed"
    assert lookup.check("uae_labour_law", "99", ["x"]) == "article_missing"
    assert lookup.check("uae_pdpl", "4", ["consent"]) == "source_missing"
    assert lookup.check("eu_ai_act", None, ["recruitment or selection"]) == "confirmed"


def test_ai_blocks_and_text_layer_check():
    raw = (
        "=== Article (9) | Probationary Period\n"
        "The employer may appoint the worker under a probationary period not exceeding six months from the start.\n"
        "=== Article 10 | Invented\n"
        "Every worker is entitled to a paid sabbatical of two full years after each month of service in the company.\n"
    )
    arts = parse_blocks(raw)
    assert [(a.article, a.title) for a in arts] == [("9", "Probationary Period"), ("10", "Invented")]
    layer = (
        "Some header\nThe employer may appoint the worker under a probationary period not exceeding six months "
        "from the start. More unrelated text follows here so the text layer is long enough to be checked. " * 5
    )
    score_against_text_layer(arts, layer)
    assert arts[0].status == "matched"
    assert arts[1].status == "unmatched"  # wording the PDF does not contain is caught


def test_ai_check_without_text_layer_is_marked_ocr():
    arts = [AIArticle("1", "", "Scanned text that cannot be cross-checked against anything at all here.")]
    score_against_text_layer(arts, "")
    assert arts[0].status == "unverified_ocr" and arts[0].coverage is None


def test_diff_reports_added_removed_changed():
    old = "Article 1\nThe period shall not exceed six months from the start of work.\nArticle 2\nThis article is repealed in the next version entirely.\n"
    new = "Article 1\nThe period shall not exceed three months from the start of work.\nArticle 3\nA brand new article about artificial intelligence systems.\n"
    d = diff_texts(old, new, src())
    assert d["added"] == ["3"] and d["removed"] == ["2"]
    assert d["changed"][0]["article"] == "1"
    assert "-The period shall not exceed six months" in d["changed"][0]["diff"]
