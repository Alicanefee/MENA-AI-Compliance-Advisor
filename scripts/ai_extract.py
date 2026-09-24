"""Transcribe a PDF into articles with Claude, then check every article against the PDF's text layer.

Use it for sources marked `extraction: ai` in config/sources.yaml (layouts that
defeat text extraction) and for scanned PDFs without a text layer (OCR).
Requires LLM_PROVIDER=anthropic and an Anthropic API key.

Usage:
    python scripts/ai_extract.py uae_labour_law
    python scripts/ai_extract.py uae_labour_law --pages-per-call 3
    python scripts/ai_extract.py --all          # every source marked extraction: ai
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from compliance.corpus.ai_extract import transcribe  # noqa: E402
from compliance.corpus.registry import load_registry  # noqa: E402
from compliance.llm import get_llm  # noqa: E402
from compliance.llm.base import LLMError  # noqa: E402
from compliance.disclaimer import short as disclaimer  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source_ids", nargs="*")
    parser.add_argument("--all", action="store_true", help="all sources marked extraction: ai")
    parser.add_argument("--pages-per-call", type=int, default=4)
    args = parser.parse_args()

    registry = load_registry()
    if args.all:
        sources = [s for s in registry.sources if s.extraction == "ai"]
    else:
        sources = [registry.get(i) for i in args.source_ids]
        if not sources or None in sources:
            parser.error("give one or more valid source ids, or --all")

    llm = get_llm()
    if not llm.available or not hasattr(llm, "read_pdf"):
        print("AI extraction needs LLM_PROVIDER=anthropic and ANTHROPIC_API_KEY (see .env.example).")
        return 2

    for source in sources:
        print(f"[{source.id}] transcribing with {llm.model}")
        try:
            result = transcribe(source, llm, args.pages_per_call)
        except (LLMError, FileNotFoundError) as exc:
            print(f"  failed: {exc}")
            continue
        counts = Counter(a["status"] for a in result["articles"])
        print(f"  {len(result['articles'])} articles: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
        for a in result["articles"]:
            if a["status"] in ("unmatched", "partial"):
                print(f"    article {a['article']:>6}  {a['status']:9} coverage {a['coverage']}")
    print("\nNext: python scripts/build_index.py  (unmatched articles are left out of the index)")
    return 0


if __name__ == "__main__":
    code = main()
    print("\n" + disclaimer())
    raise SystemExit(code)
