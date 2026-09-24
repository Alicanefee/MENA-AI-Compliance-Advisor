"""Tokenisation and normalisation shared by retrieval and verification."""
from __future__ import annotations

import re
import unicodedata

_WORD = re.compile(r"\w+", re.UNICODE)
_ARABIC_DIACRITICS = re.compile(r"[ً-ْٰـ]")
_ARABIC_ALEF = re.compile(r"[إأآا]")

STOPWORDS = frozenset(
    """a an and are as at be been by can could do does for from had has have how i if in into is it its
    may me must my no not of on or our shall should so such than that the their them then there these they
    this those to under upon was we what when where which while who will with would you your""".split()
)


def normalize(text: str) -> str:
    """Case-fold and normalise text for comparison (keeps word order)."""
    text = unicodedata.normalize("NFKC", text).casefold()
    text = _ARABIC_DIACRITICS.sub("", text)
    text = _ARABIC_ALEF.sub("ا", text).replace("ة", "ه").replace("ى", "ي")
    text = re.sub(r"[‘’`´]", "'", text)
    text = re.sub(r"[“”]", '"', text)
    text = re.sub(r"[–—]", "-", text)
    return re.sub(r"\s+", " ", text).strip()


def _stem(word: str) -> str:
    if word.endswith("ies") and len(word) > 5:
        return word[:-3] + "y"
    for suffix in ("ing", "ed"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 4:
        return word[:-1]
    return word


def tokenize(text: str) -> list[str]:
    return [_stem(t) for t in _WORD.findall(normalize(text)) if t not in STOPWORDS and len(t) > 1]
