"""Download the official legal sources listed in config/sources.yaml.

Usage:
    python scripts/fetch_laws.py              # all sources
    python scripts/fetch_laws.py --only eu_ai_act uae_pdpl
    python scripts/fetch_laws.py --list       # show status without downloading

Sources whose sites block automated downloads are reported as MANUAL with the
page to open in a browser. Save the file as data/laws/raw/<id>.pdf (or .html),
then run scripts/build_index.py.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from compliance.config import get_settings  # noqa: E402
from compliance.corpus.fetch import fetch_source, load_manifest, raw_file  # noqa: E402
from compliance.corpus.registry import load_registry  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", nargs="*", help="source ids to fetch")
    parser.add_argument("--list", action="store_true", help="list sources and local status only")
    args = parser.parse_args()

    registry = load_registry()
    sources = [s for s in registry.sources if not args.only or s.id in args.only]
    unknown = set(args.only or []) - {s.id for s in registry.sources}
    if unknown:
        print(f"Unknown source ids: {', '.join(sorted(unknown))}")
        return 2

    if args.list:
        manifest = load_manifest()
        for s in sources:
            local = raw_file(s.id)
            when = manifest.get(s.id, {}).get("retrieved_at", "-")
            print(f"{s.id:22} {s.jurisdiction}  {'present' if local else 'missing':8} {when}")
        return 0

    manual = []
    for s in sources:
        print(f"[{s.jurisdiction}] {s.id} ... ", end="", flush=True)
        result = fetch_source(s)
        print(result.status.upper(), result.detail)
        if result.status == "manual":
            manual.append(s)

    if manual:
        raw_dir = get_settings().raw_dir
        print("\nThese sources could not be downloaded automatically. Open each page in a browser,")
        print(f"download the document and save it into {raw_dir}:")
        for s in manual:
            print(f"  {s.id}.pdf  <-  {s.manual_url}")
    print("\nNext: python scripts/build_index.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
