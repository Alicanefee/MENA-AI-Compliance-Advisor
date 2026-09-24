"""Check whether the indexed laws are still current.

Re-downloads each source and compares it with the stored version. For every
source that changed, an article-level diff report is written to
data/laws/diffs/<id>/. With --summarize, an LLM adds a plain-English summary
of each diff (clearly labelled as AI-generated).

Usage:
    python scripts/check_updates.py              # check all sources
    python scripts/check_updates.py --status     # only show when each source was last checked
    python scripts/check_updates.py --summarize --rebuild

Schedule it (cron, Windows Task Scheduler or the included GitHub Actions
workflow) to be alerted when a law is amended.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from compliance.corpus.fetch import load_manifest  # noqa: E402
from compliance.corpus.registry import load_registry  # noqa: E402
from compliance.corpus.updates import STALE_AFTER_DAYS, check_source, freshness  # noqa: E402
from compliance.llm import get_llm  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--summarize", action="store_true", help="add an AI summary to each diff report")
    parser.add_argument("--rebuild", action="store_true", help="rebuild the index if anything changed")
    args = parser.parse_args()

    sources = [s for s in load_registry().sources if not args.only or s.id in args.only]
    if args.status:
        manifest = load_manifest()
        for s in sources:
            f = freshness(s, manifest)
            flag = "STALE" if f["stale"] else "ok"
            print(f"  {s.id:22} {flag:6} last checked {f['checked_at'] or 'never'}  versions {f['versions']}")
        print(f"\nSources not checked for {STALE_AFTER_DAYS} days are marked STALE.")
        return 0

    llm = get_llm() if args.summarize else None
    changed = 0
    for s in sources:
        report = check_source(s, llm)
        print(f"  {s.id:22} {report['status'].upper():15} {report.get('detail', '')}")
        if report["status"] == "changed":
            changed += 1
            d = report["diff"]
            print(f"  {'':22} added {d['added'] or '-'}  removed {d['removed'] or '-'}  changed {[c['article'] for c in d['changed']] or '-'}")
            if report.get("note"):
                print(f"  {'':22} {report['note']}")
            if report.get("ai_summary", {}).get("text"):
                print("\n" + report["ai_summary"]["text"] + "\n")

    if changed and args.rebuild:
        from compliance.corpus.store import build_passages, save_passages

        passages, _ = build_passages()
        save_passages(passages)
        print(f"\nIndex rebuilt: {len(passages)} passages")
    elif changed:
        print("\nSome sources changed. Run scripts/build_index.py and scripts/verify_content.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
