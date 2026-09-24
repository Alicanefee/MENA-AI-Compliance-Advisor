# data/

Generated locally and not committed. Layout:

| Path | Written by | Contents |
|---|---|---|
| `laws/raw/<id>.pdf\|.html` | `fetch_laws.py` or you (manual download) | Official source files |
| `laws/manifest.json` | `fetch_laws.py` | URL, hash and dates of each download, version list |
| `laws/text/<id>.txt` | `build_index.py` | Extracted plain text |
| `laws/ai_text/<id>.json` | `ai_extract.py` | AI transcription with per-article match scores |
| `laws/history/<id>/` | `fetch_laws.py` | Previous versions of changed sources |
| `laws/diffs/<id>/` | `check_updates.py` | Article-level change reports |
| `index/passages.jsonl` | `build_index.py` | Passage index used by the advisor |
| `chroma/` | `build_index.py --vector` | Optional vector index |
| `cases/cases.xlsx` | web UI / API | Case register (Cases, Documents, Log sheets) |
| `cases/<case_id>/` | web UI / API | Uploaded case documents |
| `progress.db` | web UI / API | Learner progress (SQLite) |
| `content_verification.json` | `verify_content.py` | Citation check report |

`cases/` and `progress.db` contain user data - back them up and restrict access accordingly.
