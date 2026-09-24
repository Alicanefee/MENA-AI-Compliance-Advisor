"""HTTP API and static web UI.

Run with:  uvicorn compliance.api.main:app --reload
"""
from __future__ import annotations

from collections import Counter
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from compliance import __version__, disclaimer
from compliance.agents.documents import matched_triggers
from compliance.agents.orchestrator import Advisor, detect_jurisdictions
from compliance.cases.excel_store import CaseError, CaseStore
from compliance.config import get_settings
from compliance.corpus.ai_extract import load_transcription
from compliance.corpus.fetch import load_manifest, raw_file
from compliance.corpus.lookup import CorpusLookup
from compliance.corpus.registry import load_registry
from compliance.corpus.store import load_passages
from compliance.corpus.updates import check_source, freshness, list_reports
from compliance.education.content import Catalog, check_all
from compliance.education.progress import ProgressError, ProgressStore
from compliance.llm import LLM, get_llm
from compliance.models import Answer, Passage
from compliance.retrieval.hybrid import Retriever

Lang = Literal["en", "ar"]
Jurisdiction = Literal["AE", "SA", "EU"]
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_UPLOADS = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".txt", ".csv", ".msg", ".eml"}


class AskIn(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    jurisdictions: list[Jurisdiction] | None = None
    context: str = Field(default="", max_length=4000)
    lang: Lang = "en"


class CaseIn(BaseModel):
    owner: str = Field(min_length=1, max_length=120)
    question: str = Field(min_length=3, max_length=4000)
    jurisdictions: list[Jurisdiction] | None = None
    sector: str = Field(default="", max_length=120)
    ai_use_case: str = Field(default="", max_length=2000)
    notes: str = Field(default="", max_length=4000)
    run_advisor: bool = True
    lang: Lang = "en"


class CaseUpdate(BaseModel):
    actor: str = Field(min_length=1, max_length=120)
    status: Literal["open", "in_review", "approved", "closed"] | None = None
    reviewer: str | None = Field(default=None, max_length=120)
    review_note: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=4000)


class DocumentIn(BaseModel):
    actor: str = Field(default="", max_length=120)
    name: str = Field(min_length=1, max_length=300)
    mandatory: bool = False
    due_date: str = Field(default="", pattern=r"^(\d{4}-\d{2}-\d{2})?$")


class DocumentUpdate(BaseModel):
    actor: str = Field(default="", max_length=120)
    status: Literal["missing", "received", "waived", "not_applicable"] | None = None
    due_date: str | None = Field(default=None, pattern=r"^(\d{4}-\d{2}-\d{2})?$")
    note: str | None = Field(default=None, max_length=2000)


class LearnerIn(BaseModel):
    learner_id: str
    name: str = Field(default="", max_length=120)
    lang: Lang = "en"


class QuizAnswerIn(BaseModel):
    learner_id: str
    quiz_id: str
    answer: int = Field(ge=0, le=10)
    lang: Lang = "en"


def create_app(
    passages: list[Passage] | None = None,
    llm: LLM | None = None,
    cases: CaseStore | None = None,
    progress: ProgressStore | None = None,
) -> FastAPI:
    settings = get_settings()
    passages = load_passages() if passages is None else passages
    lookup = CorpusLookup(passages)
    llm = llm or get_llm()
    advisor = Advisor(Retriever(passages), lookup, llm)
    catalog = Catalog(check_all(lookup))
    cases = cases or CaseStore()
    progress = progress or ProgressStore()
    registry = load_registry()

    app = FastAPI(title="MENA AI Compliance Advisor", version=__version__)

    def notice(data: dict, lang: str = "en") -> dict:
        """Attach the short disclaimer so it travels with API output used outside the UI."""
        return {**data, "disclaimer": disclaimer.short(lang)}

    def case_call(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except CaseError as exc:
            code = 404 if "not found" in str(exc) else 400
            raise HTTPException(code, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    # ---------------- system ----------------
    @app.get("/api/health")
    def health():
        return {
            "version": __version__,
            "passages": len(passages),
            "sources_indexed": len({p.source_id for p in passages}),
            "llm": llm.name if llm.available else "none",
            "mode": "generated" if llm.available else "extractive",
            "retrieval": "hybrid" if advisor.retriever.vector else "bm25",
        }

    @app.get("/api/disclaimer")
    def get_disclaimer(lang: Lang = "en"):
        return {"short": disclaimer.short(lang), "full": disclaimer.full(lang)}

    @app.get("/api/sources")
    def sources(lang: Lang = "en"):
        manifest = load_manifest()
        counts = Counter(p.source_id for p in passages)
        return [
            {
                "id": s.id,
                "jurisdiction": s.jurisdiction,
                "jurisdiction_name": registry.jurisdiction_name(s.jurisdiction, lang),
                "title": s.title,
                "kind": s.kind,
                "notes": s.notes,
                "manual_url": s.manual_url,
                "passages": counts.get(s.id, 0),
                "downloaded": raw_file(s.id) is not None,
                "url": manifest.get(s.id, {}).get("url") or (s.urls[0] if s.urls else s.manual_url),
                "extraction": s.extraction,
                "ai_transcription": bool(s.extraction == "ai" and load_transcription(s.id)),
                **freshness(s, manifest),
            }
            for s in registry.sources
        ]

    def _source(source_id: str):
        s = registry.get(source_id)
        if s is None:
            raise HTTPException(404, "Unknown source")
        return s

    @app.get("/api/sources/{source_id}/diffs")
    def source_diffs(source_id: str):
        return [notice(r) for r in list_reports(_source(source_id).id)]

    @app.post("/api/sources/{source_id}/check")
    def source_check(source_id: str, summarize: bool = False):
        """Re-download one source now and return a diff report if it changed.
        The running index is not modified; rebuild it to apply changes."""
        return notice(check_source(_source(source_id), llm if summarize else None))

    # ---------------- advice ----------------
    @app.post("/api/ask", response_model=Answer)
    def ask(req: AskIn):
        return advisor.ask(req.question, req.jurisdictions, req.context, req.lang)

    # ---------------- cases ----------------
    @app.post("/api/cases")
    def create_case(req: CaseIn):
        scope = req.jurisdictions or detect_jurisdictions(f"{req.question} {req.ai_use_case}")
        answer = advisor.ask(req.question, scope, req.ai_use_case, req.lang) if req.run_advisor else None
        case_id = case_call(
            cases.create_case,
            owner=req.owner,
            question=req.question,
            jurisdictions=scope,
            sector=req.sector,
            ai_use_case=req.ai_use_case,
            notes=req.notes,
            answer=answer.model_dump() if answer else None,
        )
        triggers = matched_triggers(f"{req.question} {req.ai_use_case}")
        return notice(
            {
                "case_id": case_id,
                "answer": answer.model_dump() if answer else None,
                "recommended_modules": catalog.recommend(scope, triggers, req.lang),
            },
            req.lang,
        )

    @app.get("/api/cases")
    def list_cases(status: str | None = None):
        return case_call(cases.list_cases, status)

    @app.get("/api/cases/{case_id}")
    def get_case(case_id: str, lang: Lang = "en"):
        return notice(case_call(cases.get_case, case_id), lang)

    @app.patch("/api/cases/{case_id}")
    def update_case(case_id: str, req: CaseUpdate):
        fields = req.model_dump(exclude={"actor"}, exclude_none=True)
        return notice(case_call(cases.update_case, case_id, req.actor, **fields))

    @app.post("/api/cases/{case_id}/documents")
    def add_document(case_id: str, req: DocumentIn):
        doc_id = case_call(cases.add_document, case_id, req.name, req.mandatory, req.due_date, req.actor)
        return notice({"doc_id": doc_id, "case": case_call(cases.get_case, case_id)})

    @app.patch("/api/cases/{case_id}/documents/{doc_id}")
    def update_document(case_id: str, doc_id: str, req: DocumentUpdate):
        fields = req.model_dump(exclude={"actor"}, exclude_none=True)
        return notice(case_call(cases.update_document, case_id, doc_id, req.actor, **fields))

    @app.post("/api/cases/{case_id}/documents/{doc_id}/upload")
    async def upload(case_id: str, doc_id: str, file: UploadFile = File(...)):
        name = file.filename or "upload"
        suffix = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""
        if suffix not in ALLOWED_UPLOADS:
            raise HTTPException(400, f"File type not allowed: {suffix or 'none'}")
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "File exceeds 20 MB")
        path = case_call(cases.save_upload, case_id, doc_id, name, content)
        return notice({"saved": path, "case": case_call(cases.get_case, case_id)})

    # ---------------- learning ----------------
    def progress_call(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ProgressError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.post("/api/learn/learner")
    def learner(req: LearnerIn):
        progress_call(progress.ensure_learner, req.learner_id, req.name, req.lang)
        return {"ok": True}

    @app.get("/api/learn/modules")
    def modules(lang: Lang = "en", learner_id: str | None = None):
        items = catalog.modules(lang)
        if learner_id:
            progress_call(progress.ensure_learner, learner_id, "", lang)
            for m in items:
                m["progress"] = progress.module_status(learner_id, m["id"], catalog.module_quiz_ids(m["id"]))
        return {"meta": catalog.meta(), "modules": items, "tracks": catalog.tracks(lang), "disclaimer": disclaimer.short(lang)}

    @app.get("/api/learn/modules/{module_id}")
    def module(module_id: str, lang: Lang = "en", learner_id: str | None = None):
        m = catalog.module(module_id, lang)
        if m is None:
            raise HTTPException(404, "Module not found")
        if learner_id:
            for lesson in m["lessons"]:
                progress_call(progress.record_view, learner_id, lesson["id"])
        return {**m, "disclaimer": disclaimer.short(lang)}

    @app.post("/api/learn/answer")
    def answer(req: QuizAnswerIn):
        result = catalog.grade(req.quiz_id, req.answer, req.lang)
        if result is None:
            raise HTTPException(404, "Question not found")
        progress_call(progress.record_attempt, req.learner_id, result["module_id"], req.quiz_id, req.answer, result["correct"])
        result["module_progress"] = progress.module_status(
            req.learner_id, result["module_id"], catalog.module_quiz_ids(result["module_id"])
        )
        return notice(result, req.lang)

    @app.get("/api/learn/scenarios")
    def scenario_list(lang: Lang = "en"):
        return catalog.scenario_list(lang)

    @app.get("/api/learn/scenarios/{scenario_id}")
    def scenario(scenario_id: str, lang: Lang = "en"):
        s = catalog.scenario(scenario_id, lang)
        if s is None:
            raise HTTPException(404, "Scenario not found")
        return s

    @app.get("/api/learn/scenarios/{scenario_id}/{question_id}/answer")
    def scenario_answer(scenario_id: str, question_id: str, lang: Lang = "en"):
        a = catalog.scenario_answer(scenario_id, question_id, lang)
        if a is None:
            raise HTTPException(404, "Question not found")
        return {**a, "disclaimer": disclaimer.short(lang)}

    # ---------------- web UI ----------------
    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(settings.web_dir / "index.html")

    app.mount("/static", StaticFiles(directory=settings.web_dir), name="static")
    return app


app = create_app()
