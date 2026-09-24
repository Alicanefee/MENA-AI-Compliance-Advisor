"""Curriculum and scenario content, localised and annotated with citation checks."""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Iterator

import yaml

from compliance.config import get_settings
from compliance.corpus.lookup import CorpusLookup

LANGS = ("en", "ar")


@lru_cache(maxsize=1)
def curriculum() -> dict:
    with open(get_settings().content_dir / "curriculum.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@lru_cache(maxsize=1)
def scenarios() -> dict:
    with open(get_settings().content_dir / "scenarios.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def tr(value: Any, lang: str) -> Any:
    """Pick a translation from {en: ..., ar: ...}; fall back to English."""
    if isinstance(value, dict) and "en" in value:
        return value.get(lang) or value["en"]
    return value


def cite_key(cite: dict) -> str:
    return f"{cite['source']}|{cite.get('article') or ''}|{'|'.join(cite.get('expect', []))}"


def iter_citations() -> Iterator[tuple[str, dict]]:
    """Yield (location, citation) for every cited item in the content."""
    for module in curriculum()["modules"]:
        for lesson in module["lessons"]:
            for i, point in enumerate(lesson["points"]):
                if point.get("cite"):
                    yield f"{lesson['id']} point {i + 1}", point["cite"]
        for quiz in module.get("quiz", []):
            if quiz.get("cite"):
                yield quiz["id"], quiz["cite"]
    for scenario in scenarios()["scenarios"]:
        for q in scenario["questions"]:
            for i, point in enumerate(q["points"]):
                if point.get("cite"):
                    yield f"{scenario['id']}/{q['id']} point {i + 1}", point["cite"]


def check_all(lookup: CorpusLookup) -> dict[str, str]:
    return {cite_key(c): lookup.check(c["source"], c.get("article"), c.get("expect")) for _, c in iter_citations()}


class Catalog:
    """Localised views of the content for the API."""

    def __init__(self, statuses: dict[str, str]):
        self.statuses = statuses

    def _point(self, point: dict, lang: str) -> dict:
        out = {"kind": point.get("kind", "law"), "text": tr(point["text"], lang)}
        if point.get("cite"):
            c = point["cite"]
            out["cite"] = {
                "source": c["source"],
                "article": c.get("article"),
                "check": self.statuses.get(cite_key(c), "unchecked"),
            }
        return out

    def meta(self) -> dict:
        c = curriculum()
        return {"version": c.get("version"), "reviewed_at": c.get("reviewed_at")}

    def modules(self, lang: str) -> list[dict]:
        return [
            {
                "id": m["id"],
                "level": m["level"],
                "minutes": m["minutes"],
                "prerequisites": m.get("prerequisites", []),
                "title": tr(m["title"], lang),
                "summary": tr(m.get("summary", ""), lang),
                "lessons": len(m["lessons"]),
                "quiz": len(m.get("quiz", [])),
            }
            for m in curriculum()["modules"]
        ]

    def tracks(self, lang: str) -> list[dict]:
        return [
            {"id": t["id"], "title": tr(t["title"], lang), "description": tr(t["description"], lang), "modules": t["modules"]}
            for t in curriculum()["tracks"]
        ]

    def module(self, module_id: str, lang: str) -> dict | None:
        m = next((m for m in curriculum()["modules"] if m["id"] == module_id), None)
        if m is None:
            return None
        return {
            "id": m["id"],
            "title": tr(m["title"], lang),
            "summary": tr(m.get("summary", ""), lang),
            "level": m["level"],
            "lessons": [
                {"id": les["id"], "title": tr(les["title"], lang), "points": [self._point(p, lang) for p in les["points"]]}
                for les in m["lessons"]
            ],
            # Answers are not sent until the learner submits.
            "quiz": [
                {"id": q["id"], "question": tr(q["question"], lang), "options": tr(q["options"], lang)}
                for q in m.get("quiz", [])
            ],
        }

    def quiz_item(self, quiz_id: str) -> tuple[str, dict] | None:
        for m in curriculum()["modules"]:
            for q in m.get("quiz", []):
                if q["id"] == quiz_id:
                    return m["id"], q
        return None

    def module_quiz_ids(self, module_id: str) -> list[str]:
        m = next((m for m in curriculum()["modules"] if m["id"] == module_id), None)
        return [q["id"] for q in m.get("quiz", [])] if m else []

    def grade(self, quiz_id: str, answer: int, lang: str) -> dict | None:
        found = self.quiz_item(quiz_id)
        if not found:
            return None
        module_id, q = found
        cite = q.get("cite")
        return {
            "module_id": module_id,
            "correct": answer == q["answer"],
            "answer": q["answer"],
            "explanation": tr(q.get("explanation", ""), lang),
            "cite": {
                "source": cite["source"],
                "article": cite.get("article"),
                "check": self.statuses.get(cite_key(cite), "unchecked"),
            }
            if cite
            else None,
        }

    def recommend(self, jurisdictions: list[str], triggers: set[str], lang: str) -> list[dict]:
        """Suggest modules for a case, based on its jurisdictions and matched topics."""
        wanted = ["foundations"]
        if "AE" in jurisdictions:
            if triggers & {"recruitment", "workforce", "monitoring"}:
                wanted.append("uae-labour")
            wanted.append("uae-pdpl")
        if "SA" in jurisdictions:
            wanted.append("saudi")
        if "EU" in jurisdictions:
            wanted.append("eu-ai-act")
        by_id = {m["id"]: m for m in self.modules(lang)}
        return [by_id[m] for m in wanted if m in by_id]

    def scenario_list(self, lang: str) -> list[dict]:
        return [
            {
                "id": s["id"],
                "title": tr(s["title"], lang),
                "jurisdictions": s["jurisdictions"],
                "sector": s["sector"],
                "level": s["level"],
            }
            for s in scenarios()["scenarios"]
        ]

    def scenario(self, scenario_id: str, lang: str) -> dict | None:
        s = next((s for s in scenarios()["scenarios"] if s["id"] == scenario_id), None)
        if s is None:
            return None
        return {
            "id": s["id"],
            "title": tr(s["title"], lang),
            "jurisdictions": s["jurisdictions"],
            "context": tr(s["context"], lang).strip(),
            "questions": [{"id": q["id"], "type": q["type"], "question": tr(q["question"], lang)} for q in s["questions"]],
        }

    def scenario_answer(self, scenario_id: str, question_id: str, lang: str) -> dict | None:
        s = next((s for s in scenarios()["scenarios"] if s["id"] == scenario_id), None)
        q = next((q for q in (s or {}).get("questions", []) if q["id"] == question_id), None)
        if q is None:
            return None
        return {
            "verdict": q.get("verdict"),
            "points": [self._point(p, lang) for p in q["points"]],
            "could_change": tr(q.get("could_change", []), lang),
        }
