"""Runtime settings, read once from the environment (and `.env`)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _path(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (ROOT / p).resolve()


@dataclass(frozen=True)
class Settings:
    data_dir: Path = field(default_factory=lambda: _path(os.getenv("DATA_DIR", "data")))
    config_dir: Path = ROOT / "config"
    content_dir: Path = ROOT / "content"
    web_dir: Path = ROOT / "web"

    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "none").strip().lower())
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "").strip())
    retrieval: str = field(default_factory=lambda: os.getenv("RETRIEVAL", "bm25").strip().lower())
    embeddings: str = field(default_factory=lambda: os.getenv("EMBEDDINGS", "chroma-default").strip().lower())
    openai_embed_model: str = field(
        default_factory=lambda: os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    )
    min_passage_score: float = field(default_factory=lambda: float(os.getenv("MIN_PASSAGE_SCORE", "1.0")))

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "laws" / "raw"

    @property
    def text_dir(self) -> Path:
        return self.data_dir / "laws" / "text"

    @property
    def manifest_path(self) -> Path:
        return self.data_dir / "laws" / "manifest.json"

    @property
    def index_dir(self) -> Path:
        return self.data_dir / "index"

    @property
    def chunks_path(self) -> Path:
        return self.index_dir / "passages.jsonl"

    @property
    def chroma_dir(self) -> Path:
        return self.data_dir / "chroma"

    @property
    def cases_dir(self) -> Path:
        return self.data_dir / "cases"

    @property
    def cases_workbook(self) -> Path:
        return self.cases_dir / "cases.xlsx"

    @property
    def progress_db(self) -> Path:
        return self.data_dir / "progress.db"

    @property
    def verification_path(self) -> Path:
        return self.data_dir / "content_verification.json"


def get_settings() -> Settings:
    return Settings()
