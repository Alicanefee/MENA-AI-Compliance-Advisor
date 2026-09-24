"""Learner progress in SQLite."""
from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from compliance.config import get_settings

PASS_MARK = 0.7

SCHEMA = """
CREATE TABLE IF NOT EXISTS learners (
  learner_id TEXT PRIMARY KEY,
  name TEXT,
  lang TEXT DEFAULT 'en',
  created_at TEXT
);
CREATE TABLE IF NOT EXISTS quiz_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  learner_id TEXT NOT NULL,
  module_id TEXT NOT NULL,
  quiz_id TEXT NOT NULL,
  answer INTEGER NOT NULL,
  correct INTEGER NOT NULL,
  attempted_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lesson_views (
  learner_id TEXT NOT NULL,
  lesson_id TEXT NOT NULL,
  viewed_at TEXT NOT NULL,
  PRIMARY KEY (learner_id, lesson_id)
);
"""

_LEARNER_ID = re.compile(r"^[A-Za-z0-9._@-]{1,64}$")


class ProgressError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def check_learner_id(learner_id: str) -> str:
    if not _LEARNER_ID.match(learner_id or ""):
        raise ProgressError("Learner id may contain letters, digits and . _ @ - (max 64 characters)")
    return learner_id


class ProgressStore:
    def __init__(self, path: Path | None = None):
        self.path = path or get_settings().progress_db
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._conn()) as c:
            c.executescript(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def ensure_learner(self, learner_id: str, name: str = "", lang: str = "en") -> None:
        check_learner_id(learner_id)
        with closing(self._conn()) as c, c:
            c.execute(
                "INSERT INTO learners (learner_id, name, lang, created_at) VALUES (?,?,?,?) "
                "ON CONFLICT(learner_id) DO UPDATE SET lang=excluded.lang, "
                "name=CASE WHEN excluded.name <> '' THEN excluded.name ELSE learners.name END",
                (learner_id, name, lang, _now()),
            )

    def record_view(self, learner_id: str, lesson_id: str) -> None:
        check_learner_id(learner_id)
        with closing(self._conn()) as c, c:
            c.execute(
                "INSERT OR IGNORE INTO lesson_views (learner_id, lesson_id, viewed_at) VALUES (?,?,?)",
                (learner_id, lesson_id, _now()),
            )

    def record_attempt(self, learner_id: str, module_id: str, quiz_id: str, answer: int, correct: bool) -> None:
        check_learner_id(learner_id)
        with closing(self._conn()) as c, c:
            c.execute(
                "INSERT INTO quiz_attempts (learner_id, module_id, quiz_id, answer, correct, attempted_at) "
                "VALUES (?,?,?,?,?,?)",
                (learner_id, module_id, quiz_id, answer, int(correct), _now()),
            )

    def latest_results(self, learner_id: str, module_id: str) -> dict[str, bool]:
        """Latest attempt per question in a module."""
        with closing(self._conn()) as c:
            rows = c.execute(
                "SELECT quiz_id, correct FROM quiz_attempts WHERE learner_id=? AND module_id=? ORDER BY id DESC",
                (learner_id, module_id),
            ).fetchall()
        latest: dict[str, bool] = {}
        for quiz_id, correct in rows:
            latest.setdefault(quiz_id, bool(correct))
        return latest

    def module_status(self, learner_id: str, module_id: str, quiz_ids: list[str]) -> dict:
        latest = self.latest_results(learner_id, module_id)
        answered = [q for q in quiz_ids if q in latest]
        score = sum(latest[q] for q in answered) / len(quiz_ids) if quiz_ids else 0.0
        return {
            "answered": len(answered),
            "total": len(quiz_ids),
            "score": round(score, 3),
            "completed": bool(quiz_ids) and len(answered) == len(quiz_ids) and score >= PASS_MARK,
        }
