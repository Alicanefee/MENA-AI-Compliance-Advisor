"""Download official sources and keep a manifest of what was retrieved.

Downloads identify the tool honestly in the User-Agent. Sites that block
automated clients are not worked around: the source is reported as
`manual` together with the page to open in a browser.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests

from compliance.config import get_settings
from compliance.corpus.registry import Source

USER_AGENT = "uae-ai-compliance/0.1 (+https://github.com/Alicanefee/uae-ai-compliance)"
MIN_INTERVAL_S = 2.0
TIMEOUT_S = 90

_last_request = 0.0


@dataclass
class FetchResult:
    source_id: str
    status: str  # downloaded | unchanged | manual | error
    path: Path | None = None
    url: str = ""
    detail: str = ""


def _polite_get(url: str, accept: str) -> requests.Response:
    global _last_request
    wait = MIN_INTERVAL_S - (time.monotonic() - _last_request)
    if wait > 0:
        time.sleep(wait)
    _last_request = time.monotonic()
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en"}
    headers["Accept"] = accept or "application/pdf,text/html,application/xhtml+xml;q=0.9,*/*;q=0.5"
    return requests.get(url, headers=headers, timeout=TIMEOUT_S, allow_redirects=True)


def _detect_kind(resp: requests.Response) -> str | None:
    body = resp.content
    if body[:5] == b"%PDF-":
        return "pdf"
    ctype = resp.headers.get("Content-Type", "").lower()
    if ("html" in ctype or "xml" in ctype) and len(body) > 2000:
        return "html"
    return None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest() -> dict:
    path = get_settings().manifest_path
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_manifest(manifest: dict) -> None:
    path = get_settings().manifest_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def history_dir(source_id: str) -> Path:
    return get_settings().data_dir / "laws" / "history" / source_id


def archive_version(source_id: str, raw: Path, digest: str) -> None:
    """Keep the replaced raw file and its extracted text so changes can be diffed."""
    folder = history_dir(source_id)
    folder.mkdir(parents=True, exist_ok=True)
    stem = digest[:12]
    (folder / f"{stem}{raw.suffix}").write_bytes(raw.read_bytes())
    text = get_settings().text_dir / f"{source_id}.txt"
    if text.exists():
        (folder / f"{stem}.txt").write_text(text.read_text(encoding="utf-8"), encoding="utf-8")


def raw_file(source_id: str) -> Path | None:
    """Return the raw file for a source, whether downloaded or placed manually."""
    raw_dir = get_settings().raw_dir
    for ext in (".pdf", ".html"):
        candidate = raw_dir / f"{source_id}{ext}"
        if candidate.exists():
            return candidate
    return None


def fetch_source(source: Source) -> FetchResult:
    raw_dir = get_settings().raw_dir
    raw_dir.mkdir(parents=True, exist_ok=True)
    errors = []
    for url in source.urls:
        try:
            resp = _polite_get(url, source.accept)
        except requests.RequestException as exc:
            errors.append(f"{url}: {exc.__class__.__name__}")
            continue
        if resp.status_code != 200:
            errors.append(f"{url}: HTTP {resp.status_code}")
            continue
        kind = _detect_kind(resp)
        if kind is None:
            errors.append(f"{url}: unexpected content ({resp.headers.get('Content-Type', '?')})")
            continue

        target = raw_dir / f"{source.id}.{kind}"
        previous = raw_file(source.id)
        old_hash = sha256(previous) if previous else None
        new_hash = hashlib.sha256(resp.content).hexdigest()
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        manifest = load_manifest()
        entry = manifest.get(source.id, {})
        if old_hash != new_hash:
            if previous:
                archive_version(source.id, previous, old_hash)
                if previous != target:
                    previous.unlink()
            target.write_bytes(resp.content)
            entry.setdefault("versions", []).append({"sha256": new_hash, "retrieved_at": now, "url": url})
            entry.update(retrieved_at=now, previous_sha256=old_hash)
        entry.update(url=url, checked_at=now, sha256=new_hash, bytes=len(resp.content))
        manifest[source.id] = entry
        save_manifest(manifest)
        if old_hash == new_hash:
            return FetchResult(source.id, "unchanged", target, url)
        return FetchResult(source.id, "downloaded", target, url, "content changed" if old_hash else "")

    if raw_file(source.id):
        return FetchResult(source.id, "error", raw_file(source.id), detail="; ".join(errors) + " (keeping existing file)")
    return FetchResult(source.id, "manual", None, detail="; ".join(errors) or "no URL configured")
