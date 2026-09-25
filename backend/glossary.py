"""Task 3.8: Reviewed financial glossary and language support metadata.

Guarantees financial and legal terms (e.g. 'moratorium', 'margin money')
are never corrupted by machine translation, per SPEC.md section 8.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_PATH = ROOT / "data" / "financial_glossary.json"

COMPLETE_LANGUAGES = ["en", "ta", "hi"]
PLANNED_LANGUAGES = ["te", "kn", "bn", "mr", "gu", "ml"]

ALL_LANGUAGES = {
    "en": {"name": "English", "native": "English", "status": "complete"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "status": "complete"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "status": "complete"},
    "te": {"name": "Telugu", "native": "తెలుగు", "status": "planned"},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "status": "planned"},
    "bn": {"name": "Bengali", "native": "বাংলা", "status": "planned"},
    "mr": {"name": "Marathi", "native": "मराठी", "status": "planned"},
    "gu": {"name": "Gujarati", "native": "ગુજરાતી", "status": "planned"},
    "ml": {"name": "Malayalam", "native": "മലയാളം", "status": "planned"},
}


def load_glossary() -> dict[str, Any]:
    if not GLOSSARY_PATH.exists():
        return {}
    with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("terms", {})


_GLOSSARY_TERMS: dict[str, Any] | None = None


def get_glossary() -> dict[str, Any]:
    global _GLOSSARY_TERMS
    if _GLOSSARY_TERMS is None:
        _GLOSSARY_TERMS = load_glossary()
    return _GLOSSARY_TERMS


def get_term(term_key: str, lang: str = "en") -> str | None:
    terms = get_glossary()
    term = terms.get(term_key)
    if not term:
        return None
    return term.get(lang) or term.get("en")


def is_language_complete(lang: str) -> bool:
    return lang in COMPLETE_LANGUAGES


def is_language_planned(lang: str) -> bool:
    return lang in PLANNED_LANGUAGES


def get_language_status(lang: str) -> str:
    meta = ALL_LANGUAGES.get(lang)
    if not meta:
        return "unknown"
    return meta["status"]


def protect_financial_terms(text: str, target_lang: str) -> str:
    """Replace English financial terms with reviewed terminology in target language."""
    if not text or target_lang == "en":
        return text

    terms = get_glossary()
    result = text
    for term_key, term in terms.items():
        if not term.get("do_not_machine_translate"):
            continue
        en_val = term.get("en")
        target_val = term.get(target_lang)
        if en_val and target_val and en_val.lower() in result.lower():
            # Case-insensitive replacement
            import re
            pattern = re.compile(re.escape(en_val), re.IGNORECASE)
            result = pattern.sub(target_val, result)
    return result
