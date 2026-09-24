"""Document checklist from deterministic rules (`config/documents.yaml`)."""
from __future__ import annotations

import re
from functools import lru_cache

import yaml

from compliance.config import get_settings
from compliance.corpus.lookup import CorpusLookup
from compliance.models import RequiredDocument
from compliance.retrieval.text import normalize


@lru_cache(maxsize=1)
def load_rules() -> dict:
    with open(get_settings().config_dir / "documents.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def matched_triggers(text: str) -> set[str]:
    norm = normalize(text)
    hits = set()
    for name, keywords in load_rules()["triggers"].items():
        if any(re.search(rf"(?<!\w){re.escape(normalize(k))}(?!\w)", norm) for k in keywords):
            hits.add(name)
    return hits


def required_documents(text: str, jurisdictions: list[str], lookup: CorpusLookup) -> list[RequiredDocument]:
    triggers = matched_triggers(text)
    out = []
    for rule in load_rules()["documents"]:
        if rule["jurisdiction"] not in jurisdictions or not triggers & set(rule["triggers"]):
            continue
        basis = [
            {
                "source": b["source"],
                "article": b.get("article"),
                "check": lookup.check(b["source"], b.get("article"), b.get("expect")),
            }
            for b in rule.get("basis", [])
        ]
        out.append(
            RequiredDocument(
                id=rule["id"],
                name=rule["name"],
                mandatory=bool(rule.get("mandatory")),
                why=rule["why"],
                basis=basis,
                kind=rule.get("kind", "legal"),
            )
        )
    return out
