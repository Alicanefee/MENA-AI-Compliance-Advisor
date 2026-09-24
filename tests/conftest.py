import json
import os
import sys
import tempfile
from pathlib import Path

# Isolate all file output before any project module reads its settings.
_TMP = tempfile.mkdtemp(prefix="aca-tests-")
os.environ["DATA_DIR"] = _TMP
os.environ["LLM_PROVIDER"] = "none"
os.environ["RETRIEVAL"] = "bm25"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

from compliance.corpus.chunker import make_passage  # noqa: E402
from compliance.corpus.registry import load_registry  # noqa: E402

# Synthetic passages for tests. The wording is written for the tests and is NOT
# the text of any law.
FIXTURE = [
    ("uae_labour_law", "4", "Equality and Non-discrimination",
     "Test fixture. Any discrimination on the basis of race, colour, sex, religion, national or social origin or "
     "disability which impairs equality of opportunity in employment is prohibited."),
    ("uae_labour_law", "8", "Employment Contract",
     "Test fixture. The contract shall be made in two copies; one copy is kept by the employer and the other is "
     "handed over to the worker."),
    ("uae_labour_law", "9", "Probationary Period",
     "Test fixture. The employer may appoint the worker under a probationary period not exceeding (6) six months."),
    ("sa_pdpl", "29", "",
     "Test fixture. A controller may transfer personal data outside the Kingdom only for the purposes listed in this "
     "article and subject to the regulations."),
    ("eu_ai_act", "5", "Prohibited AI practices",
     "Test fixture. The use of AI systems to infer emotions of a natural person in the areas of workplace and "
     "education institutions is prohibited, except where intended for medical or safety reasons."),
    ("eu_ai_act", "Annex III", "",
     "Test fixture. High-risk areas include employment: AI systems intended to be used for the recruitment or "
     "selection of natural persons, in particular to filter applications and evaluate candidates."),
]


@pytest.fixture
def passages():
    registry = load_registry()
    return [make_passage(registry.get(sid), art, head, text, 0) for sid, art, head, text in FIXTURE]


class FakeLLM:
    """Deterministic stand-in for the analyst and challenger agents."""

    name = "fake"
    model = "fake-model"

    def __init__(self, analyst: dict, challenger: dict):
        self.responses = [json.dumps(analyst), json.dumps(challenger)]

    @property
    def available(self) -> bool:
        return True

    def complete(self, system: str, user: str, max_tokens: int = 16000) -> str:
        return self.responses.pop(0)


@pytest.fixture
def fake_llm_factory():
    return FakeLLM


@pytest.fixture
def tmp_data(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    return tmp_path
