"""Extract text from downloaded sources, split into article passages and build the index.

Usage:
    python scripts/build_index.py            # BM25 index (passages.jsonl)
    python scripts/build_index.py --vector   # also (re)build the ChromaDB vector index
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from compliance.corpus.store import build_passages, save_passages  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--vector", action="store_true", help="also build the ChromaDB vector index")
    args = parser.parse_args()

    passages, reports = build_passages()
    for r in reports:
        if r.status == "missing":
            print(f"  {r.source_id:22} MISSING  (run scripts/fetch_laws.py or place the file manually)")
        else:
            print(f"  {r.source_id:22} {r.passages:4} passages  {r.articles:4} articles  {r.chars:8} chars")
            if r.detail:
                print(f"  {'':22} {r.detail}")
    path = save_passages(passages)
    print(f"\n{len(passages)} passages written to {path}")

    if args.vector:
        from compliance.retrieval.vector import rebuild

        print(f"Vector index: {rebuild(passages)} passages embedded")
    print("Next: python scripts/verify_content.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
