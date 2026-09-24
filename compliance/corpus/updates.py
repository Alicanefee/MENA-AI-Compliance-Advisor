"""Keeping the corpus current: freshness status, re-checks and article-level diffs.

A check re-downloads a source. If the file changed, the previous version is
archived (see fetch.archive_version) and a diff report is written to
`data/laws/diffs/<id>/<timestamp>.json`, listing added, removed and changed
articles with a unified diff for each change. An optional AI summary of the
report is stored next to it and labelled as generated.
"""
from __future__ import annotations

import difflib
import json
from datetime import datetime, timezone
from pathlib import Path

from compliance.config import get_settings
from compliance.corpus.chunker import chunk_text
from compliance.corpus.extract import extract
from compliance.corpus.fetch import fetch_source, history_dir, load_manifest, raw_file
from compliance.corpus.registry import Source
from compliance.llm.base import LLMError
from compliance.retrieval.text import normalize

STALE_AFTER_DAYS = 90
MAX_DIFF_LINES = 80


def freshness(source: Source, manifest: dict | None = None) -> dict:
    entry = (manifest if manifest is not None else load_manifest()).get(source.id, {})
    checked = entry.get("checked_at") or entry.get("retrieved_at")
    age = None
    if checked:
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(checked)).days
    return {
        "retrieved_at": entry.get("retrieved_at"),
        "checked_at": checked,
        "days_since_check": age,
        "stale": age is None or age > STALE_AFTER_DAYS,
        "versions": len(entry.get("versions", [])),
    }


def _articles(text: str, source: Source) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in chunk_text(text, source):
        out[p.article] = (out.get(p.article, "") + "\n" + p.text).strip()
    return out


def diff_texts(old: str, new: str, source: Source) -> dict:
    before, after = _articles(old, source), _articles(new, source)
    changed = []
    for art in sorted(before.keys() & after.keys(), key=_order):
        if normalize(before[art]) == normalize(after[art]):
            continue
        lines = list(
            difflib.unified_diff(
                before[art].splitlines(), after[art].splitlines(), "previous", "current", lineterm="", n=1
            )
        )
        changed.append(
            {
                "article": art,
                "similarity": round(difflib.SequenceMatcher(None, before[art], after[art]).ratio(), 3),
                "diff": "\n".join(lines[:MAX_DIFF_LINES]) + ("\n..." if len(lines) > MAX_DIFF_LINES else ""),
            }
        )
    return {
        "added": sorted(after.keys() - before.keys(), key=_order),
        "removed": sorted(before.keys() - after.keys(), key=_order),
        "changed": changed,
        "unchanged": len(before.keys() & after.keys()) - len(changed),
    }


def diffs_dir(source_id: str) -> Path:
    return get_settings().data_dir / "laws" / "diffs" / source_id


def list_reports(source_id: str) -> list[dict]:
    folder = diffs_dir(source_id)
    if not folder.exists():
        return []
    reports = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("*.json"), reverse=True)]
    return reports


def check_source(source: Source, llm=None) -> dict:
    """Re-download one source; on change, write and return a diff report."""
    result = fetch_source(source)
    report = {
        "source_id": source.id,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": result.status,
        "detail": result.detail,
        "url": result.url,
    }
    if result.status != "downloaded":
        return report

    manifest = load_manifest().get(source.id, {})
    old_text = _previous_text(source, manifest.get("previous_sha256"))
    if old_text is None:
        report["status"] = "first_download"
        return report

    report.update(
        status="changed",
        previous_sha256=manifest.get("previous_sha256"),
        current_sha256=manifest.get("sha256"),
        diff=diff_texts(old_text, extract(raw_file(source.id), source.trim), source),
        rebuild_required=True,
    )
    if source.extraction == "ai":
        report["note"] = "The AI transcription no longer matches the PDF; rerun scripts/ai_extract.py."
    if llm is not None and getattr(llm, "available", False):
        report["ai_summary"] = summarize(llm, source, report["diff"])

    folder = diffs_dir(source.id)
    folder.mkdir(parents=True, exist_ok=True)
    stamp = report["checked_at"].replace(":", "").replace("-", "")
    (folder / f"{stamp}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def _previous_text(source: Source, digest: str | None) -> str | None:
    if not digest:
        return None
    folder, stem = history_dir(source.id), digest[:12]
    if (folder / f"{stem}.txt").exists():
        return (folder / f"{stem}.txt").read_text(encoding="utf-8")
    for ext in (".pdf", ".html"):
        if (folder / f"{stem}{ext}").exists():
            return extract(folder / f"{stem}{ext}", source.trim)
    return None


SUMMARY_SYSTEM = (
    "You summarise changes between two versions of an official legal text for compliance staff. "
    "Describe only what the diff shows, article by article, in plain English. Do not speculate about "
    "reasons, effective dates or consequences that the diff does not state. If a change looks like "
    "formatting or extraction noise rather than wording, say so."
)


def summarize(llm, source: Source, diff: dict) -> dict:
    body = json.dumps(diff, ensure_ascii=False, indent=1)[:60000]
    try:
        text = llm.complete(SUMMARY_SYSTEM, f"SOURCE: {source.title}\n\nDIFF REPORT (JSON):\n{body}", max_tokens=4000)
    except LLMError as exc:
        return {"error": str(exc)}
    return {"generated_by": getattr(llm, "model", llm.name), "text": text.strip(), "label": "AI-generated summary - check against the diff"}


def _order(article: str) -> tuple:
    digits = "".join(ch for ch in article if ch.isdigit())
    return (0, int(digits), article) if digits else (1, 0, article)
