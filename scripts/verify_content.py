"""Check every citation in the curriculum, scenarios and document rules against the indexed official texts.

A citation is `confirmed` when the cited article exists and contains all of its
`expect` phrases. Anything else needs human review before the content is used.

Usage:
    python scripts/verify_content.py          # report
    python scripts/verify_content.py --strict # exit 1 unless every citation is confirmed
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from compliance.agents.documents import load_rules  # noqa: E402
from compliance.config import get_settings  # noqa: E402
from compliance.corpus.lookup import CorpusLookup  # noqa: E402
from compliance.corpus.store import load_passages  # noqa: E402
from compliance.education.content import iter_citations  # noqa: E402
from compliance.disclaimer import short as disclaimer  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    lookup = CorpusLookup(load_passages())
    rows = list(iter_citations())
    for rule in load_rules()["documents"]:
        for b in rule.get("basis", []):
            rows.append((f"documents/{rule['id']}", b))

    report = []
    for where, cite in rows:
        status = lookup.check(cite["source"], cite.get("article"), cite.get("expect"))
        report.append({"where": where, **cite, "status": status})
        if status != "confirmed":
            art = f" art. {cite['article']}" if cite.get("article") else ""
            print(f"  {status:16} {where:36} {cite['source']}{art}  expect={cite.get('expect')}")

    counts = Counter(r["status"] for r in report)
    print("\n" + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    out = get_settings().verification_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Report written to {out}")
    return 1 if args.strict and counts.get("confirmed", 0) != len(report) else 0


if __name__ == "__main__":
    code = main()
    print("\n" + disclaimer())
    raise SystemExit(code)
